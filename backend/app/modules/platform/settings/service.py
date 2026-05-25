from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.api.errors import ERROR_REGISTRY
from app.core.config import settings
from app.modules.platform.access_sessions.service import (
    ACCESS_SESSION_TIMEOUT,
    ACCESS_SESSION_TIMEOUT_SWEEP_LIMIT,
)
from app.modules.platform.game_codes import ALLOWED_GAME_CODES
from app.modules.platform.table_sessions.service import (
    TABLE_SESSION_DEFAULT_CHIPS,
    TABLE_SESSION_MAX_CHIPS,
)


SourceOfTruth = str
Visibility = str
RiskClass = str
RestartRequired = str
AuditRequired = str
MaskingRule = str

VISIBILITIES = {"hidden", "masked", "read_only", "editable_future"}
RESTART_VALUES = {"yes", "no", "unknown"}
AUDIT_VALUES = {"yes", "no", "future"}
MASKING_RULES = {"none", "full", "partial", "count_only", "hash_only"}
RISK_CLASSES = {"low", "medium", "high", "critical"}
SOURCES = {"env", "code", "db", "registry", "title_config", "document", "derived"}
STATUSES = {"ok", "gap", "pending"}


@dataclass(frozen=True)
class SettingsDescriptor:
    key: str
    label: str
    source_of_truth: SourceOfTruth
    owner: str
    visibility: Visibility
    risk_class: RiskClass
    environment_scope: str
    restart_required: RestartRequired
    audit_required: AuditRequired
    editable_now: bool
    masking_rule: MaskingRule
    evidence: str
    category: str
    status: str = "ok"
    notes: tuple[str, ...] = ()
    editable_when: str | None = None
    value_reader: Callable[[], object | None] | None = None


@dataclass(frozen=True)
class GapRisk:
    key: str
    severity: str
    impact: str
    mvp_mitigation: str
    long_term_mitigation: str
    follow_up_wp: str
    evidence: str


REPO_ROOT = Path(__file__).resolve().parents[5]


GAP_RISKS: tuple[GapRisk, ...] = (
    GapRisk(
        key="site_access.client_default",
        severity="critical",
        impact="A client-side default access password can leak an access-control secret and normalize unsafe registration behavior.",
        mvp_mitigation="Closed: the registration form now asks for an access code and no longer embeds a default value.",
        long_term_mitigation="Replace the shared access code with temporary invite tokens or a fully server-mediated registration flow.",
        follow_up_wp="WP-FRONTEND-SECRET-AUDIT",
        evidence="frontend/app/ui/player-register-page.tsx",
    ),
    GapRisk(
        key="health.ready_db_redis",
        severity="high",
        impact="/ready can report ready while DB or Redis dependencies are unavailable, producing false operational health.",
        mvp_mitigation="Closed: /ready now checks app, database and Redis before reporting ready.",
        long_term_mitigation="Add deeper dependency telemetry and environment-specific readiness thresholds when operations mature.",
        follow_up_wp="WP-HEALTH-READINESS-DB-REDIS",
        evidence="backend/app/api/routes/health.py",
    ),
    GapRisk(
        key="auth.rbac_fallback",
        severity="critical",
        impact="Treating an admin without profile as superadmin can become privilege escalation if profile creation drifts.",
        mvp_mitigation="Closed: admin endpoints now require an explicit admin profile; missing profile is forbidden.",
        long_term_mitigation="Add an admin-profile repair/report tool for operations without granting implicit privileges.",
        follow_up_wp="WP-AUTH-RBAC-EXPLICIT-PROFILE",
        evidence="backend/app/api/dependencies.py",
    ),
    GapRisk(
        key="cms_v2_lab.admin_token_in_query",
        severity="high",
        impact="Passing an admin token through URL query can expose it through browser history, referrers, logs, or screenshots.",
        mvp_mitigation="Closed: the lab link opens without putting the admin token in the URL.",
        long_term_mitigation="When CMS v2 is rescued, use postMessage, a one-time server token, or an httpOnly cookie handoff.",
        follow_up_wp="WP-CMS-V2-LAB-TOKEN-HANDOFF",
        evidence="frontend/app/ui/admin-shell-panel.tsx",
    ),
)


SETTING_EXPLANATIONS: dict[str, dict[str, str]] = {
    "app.name": {
        "it": "Nome leggibile dell'applicazione backend. Serve a capire quale servizio sta rispondendo quando guardi health check, log o schermate operative. Non cambia il gioco, ma aiuta a non confondere ambienti diversi.",
        "en": "Human-readable backend application name. It helps identify which service is answering in health checks, logs and operational screens. It does not change gameplay.",
    },
    "app.version": {
        "it": "Versione dichiarata del backend. E' utile per capire se stai guardando una build aggiornata o un servizio rimasto indietro dopo un deploy.",
        "en": "Declared backend version. It helps verify whether the running service matches the expected build after a deployment.",
    },
    "app.env": {
        "it": "Ambiente applicativo, per esempio sviluppo, test o produzione. E' importante per evitare di trattare un ambiente locale come se fosse produzione, o viceversa.",
        "en": "Application environment, such as development, test or production. It prevents mixing local and production assumptions.",
    },
    "api.v1_prefix": {
        "it": "Prefisso pubblico delle API versione 1. Il frontend costruisce le chiamate verso il backend assumendo questo percorso; se cambia, vanno riallineati routing e proxy.",
        "en": "Public prefix for version 1 API routes. The frontend and proxies must agree on this path.",
    },
    "database.url": {
        "it": "Stringa di connessione al database. Contiene credenziali e host, quindi non viene mai mostrata. Se non e' configurata correttamente, wallet, round, backoffice e catalogo non possono funzionare.",
        "en": "Database connection string. It contains credentials and host information, so it is never displayed. Wallets, rounds, backoffice and catalog data depend on it.",
    },
    "redis.url": {
        "it": "Indirizzo Redis usato per componenti veloci o temporanei. Anche se oggi il prodotto e' ancora piccolo, readiness e servizi devono sapere se Redis e' raggiungibile.",
        "en": "Redis endpoint for fast or temporary platform services. Readiness and runtime services need to know whether it is reachable.",
    },
    "jwt.secret": {
        "it": "Segreto usato per firmare i token di accesso. Se cambia, i token gia' salvati nei browser scadono. E' nascosto perche' chi lo conosce potrebbe falsificare sessioni.",
        "en": "Secret used to sign access tokens. Existing browser tokens expire if it changes. It is hidden because exposure could allow forged sessions.",
    },
    "jwt.access_ttl_minutes": {
        "it": "Durata dei token di accesso. Un valore troppo lungo aumenta il rischio se un token viene rubato; un valore troppo corto rende fastidiosa l'esperienza utente.",
        "en": "Access token lifetime. Longer values increase stolen-token risk; shorter values can make the user experience annoying.",
    },
    "game_launch.token_ttl_minutes": {
        "it": "Durata del token che autorizza l'ingresso in un gioco real. Deve essere breve: serve a lanciare la sessione, non a rimanere valido per sempre.",
        "en": "Lifetime of the token that authorizes launching a real-money game. It should be short and only cover the launch handshake.",
    },
    "game_launch.signing_key": {
        "it": "Chiave separata futura per firmare i token di lancio gioco. Oggi il sistema usa il percorso JWT esistente; separarla ridurra' il raggio di impatto di un segreto compromesso.",
        "en": "Future separate signing key for game launch tokens. Today launch tokens use the existing JWT path; separating it would reduce blast radius.",
    },
    "site_access.password": {
        "it": "Codice di accesso lato server per la registrazione o l'accesso controllato. E' nascosto: deve stare sul server, non nel browser.",
        "en": "Server-side access code for controlled registration or access. It is hidden and must stay server-side.",
    },
    "site_access.client_default": {
        "it": "Controlla che il frontend non incorpori un codice di accesso predefinito. Ora l'utente deve inserirlo: cosi' non lasciamo un segreto scritto nel bundle del browser.",
        "en": "Checks that the frontend does not embed a default access code. The user now has to enter it, so the browser bundle no longer carries this secret.",
    },
    "mines.server_seed": {
        "it": "Seed server per la fairness di Mines. E' un valore sensibile: serve a rendere verificabile il gioco, ma non deve essere leggibile prima del momento corretto.",
        "en": "Server seed for Mines fairness. It supports verifiability but must not be exposed before the proper reveal moment.",
    },
    "cors.allowed_origins": {
        "it": "Elenco dei siti autorizzati a chiamare il backend dal browser. Lo mostriamo solo come conteggio per evitare di esporre dettagli non necessari.",
        "en": "List of browser origins allowed to call the backend. It is shown as a count to avoid exposing unnecessary environment details.",
    },
    "assets.storage_root": {
        "it": "Cartella dove il backend salva asset caricati dal backoffice. E' mascherata per non pubblicare percorsi interni della macchina o del container.",
        "en": "Folder where uploaded backoffice assets are stored. It is masked to avoid exposing internal machine or container paths.",
    },
    "assets.public_base_url": {
        "it": "Base URL pubblica da cui il frontend legge gli asset runtime. Se e' sbagliata, immagini, skin o media possono non caricarsi.",
        "en": "Public base URL used by the frontend to read runtime assets. If wrong, images, skins or media may fail to load.",
    },
    "access_session.timeout": {
        "it": "Tempo massimo di una sessione tavolo/accesso prima della chiusura automatica. E' finanziariamente importante: evita sessioni sospese all'infinito.",
        "en": "Maximum lifetime for a table/access session before automatic closure. It matters financially because it prevents sessions from staying open forever.",
    },
    "access_session.sweep_interval": {
        "it": "Ogni quanti secondi il backend controlla le sessioni scadute. Piu' e' frequente, prima chiude i sospesi; troppo frequente pero' aumenta lavoro inutile.",
        "en": "How often the backend checks for expired sessions. More frequent checks close stale sessions sooner but add overhead.",
    },
    "access_session.sweep_limit": {
        "it": "Numero massimo di sessioni scadute gestite per ogni giro dello sweeper. Serve a controllare il carico se si accumulano molti sospesi.",
        "en": "Maximum number of expired sessions processed per sweeper run. It limits load if many stale sessions accumulate.",
    },
    "table_session.max_chips": {
        "it": "Massimo importo che puo' entrare in una sessione tavolo. E' una protezione critica: evita che il player entri accidentalmente con tutto il saldo.",
        "en": "Maximum amount that can enter a table session. It is a critical protection against accidentally bringing the full wallet balance into play.",
    },
    "table_session.default_chips": {
        "it": "Importo precompilato quando si apre una sessione tavolo. Deve essere comodo ma non pericoloso; oggi coincide con il massimo approvato.",
        "en": "Default amount prefilled when opening a table session. It should be convenient but not dangerous; today it matches the approved maximum.",
    },
    "demo.token_rate_limit": {
        "it": "Limite futuro per evitare abuso nella creazione di token demo. Oggi e' un valore di codice: prima di renderlo modificabile serve una policy con audit.",
        "en": "Future limit against demo token abuse. Today it is code-backed; an audited policy is needed before editing it in backoffice.",
    },
    "game_registry.backends": {
        "it": "Lista canonica dei giochi riconosciuti dal backend. E' la sorgente principale: frontend, finance, replay e backoffice devono allinearsi a questa lista.",
        "en": "Canonical list of games recognized by the backend. Frontend, finance, replay and backoffice adapters must align to it.",
    },
    "catalog.publication_flags": {
        "it": "Stato di pubblicazione dei titoli nel catalogo. Dice se un gioco/variante puo' comparire nel sito, ma questa schermata mostra solo la capability, non tutta la tabella live.",
        "en": "Publication state for catalog titles. It controls whether a game/variant can appear on the site; this screen only reports the capability, not the full live table.",
    },
    "health.ready_db_redis": {
        "it": "Controllo readiness di database e Redis. Ora /ready diventa verde solo se processo, DB e Redis rispondono: evita falsi positivi operativi.",
        "en": "Readiness check for database and Redis. /ready is green only when the process, DB and Redis answer, avoiding operational false positives.",
    },
    "auth.rbac_fallback": {
        "it": "Controllo che un admin senza profilo esplicito non venga promosso automaticamente a superadmin. Ora senza profilo si riceve forbidden: i permessi devono essere dichiarati.",
        "en": "Checks that an admin without an explicit profile is not automatically treated as superadmin. Missing profile is now forbidden.",
    },
    "cms_v2_lab.admin_token_in_query": {
        "it": "Controllo che il link al laboratorio Site v2 non passi il token admin nella URL. Ora il link apre il lab senza token: quando il CMS v2 verra' ripreso, andra' fatto un handoff sicuro.",
        "en": "Checks that the Site v2 lab link does not pass the admin token in the URL. The lab now opens without a token; a safe handoff is required when CMS v2 resumes.",
    },
    "error_registry.status": {
        "it": "Stato del registro errori CK.*. Serve a vedere quali codici errore ufficiali esistono, con status HTTP, messaggio, retry e livello log.",
        "en": "Status of the CK.* error registry. It shows official error codes with HTTP status, message, retryability and log level.",
    },
    "frontend.api_base_url": {
        "it": "Base URL usata dal frontend per chiamare il backend. E' build-time: se cambia, normalmente va ricostruito o riallineato il frontend.",
        "en": "Base URL used by the frontend to call the backend. It is build-time configuration and usually requires rebuilding or realigning the frontend.",
    },
    "i18n.allowed_locales": {
        "it": "Lingue supportate dai manifest dei giochi. Oggi il pattern di prodotto e' it, en, de, es; ogni nuovo gioco deve coprire lo stesso set se non deciso diversamente.",
        "en": "Locales supported by game copy manifests. Current product pattern is it, en, de, es; new games should cover the same set unless explicitly decided otherwise.",
    },
    "mines.payout_runtime_path": {
        "it": "Dove vive la logica payout runtime di Mines. E' critico per controlli finance/replay: il report deve sapere quale motore ha calcolato il risultato.",
        "en": "Where Mines payout runtime logic lives. Finance and replay checks need to know which engine calculated the result.",
    },
    "boxe.payout_runtime_path": {
        "it": "Dove vive la logica payout runtime di BOXE. Serve a collegare round, replay e spiegazione finanziaria al motore corretto.",
        "en": "Where BOXE payout runtime logic lives. It links rounds, replay and financial explanation to the correct engine.",
    },
    "hi_lo.payout_runtime_path": {
        "it": "Dove vive la logica payout runtime di HI-LO. Serve a evitare fallback Mines/BOXE e a mantenere ogni gioco responsabile della propria matematica.",
        "en": "Where HI-LO payout runtime logic lives. It avoids Mines/BOXE fallbacks and keeps each game responsible for its own math.",
    },
    "finance.replay_retention": {
        "it": "Politica generale di conservazione replay/report finanziari. Oggi dice 30 giorni online e cold storage da decidere: e' un tema legale/prodotto, non solo tecnico.",
        "en": "General retention policy for replay and financial reports. Today it says 30 days online and cold storage TBD; this is legal/product, not only technical.",
    },
    "replay.retention_online_days": {
        "it": "Numero di giorni in cui il replay resta disponibile online. Oggi e' 30: abbastanza per supporto e verifiche rapide, senza promettere archivio infinito.",
        "en": "Number of days replay stays available online. Today it is 30: enough for support and quick checks without promising infinite online storage.",
    },
    "replay.retention_cold_storage": {
        "it": "Durata e forma dello storage freddo dei replay. E' ancora da decidere con criteri legali e operativi; per questo resta pending.",
        "en": "Duration and shape of cold storage for replays. It still needs legal and operational decisions, so it remains pending.",
    },
    "crypto_wallet.enabled": {
        "it": "Indicatore futuro per un eventuale wallet crypto. Resta pending e non modificabile: prima servono compliance, custody, ledger e responsabilita' operative.",
        "en": "Future indicator for a possible crypto wallet. It remains pending and not editable until compliance, custody, ledger and operational ownership are defined.",
    },
}


SETTINGS_DESCRIPTORS: tuple[SettingsDescriptor, ...] = (
    SettingsDescriptor(
        key="app.name",
        label="Application name",
        source_of_truth="env",
        owner="platform",
        visibility="read_only",
        risk_class="low",
        environment_scope="all",
        restart_required="yes",
        audit_required="no",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:12",
        category="Environment",
        value_reader=lambda: settings.app_name,
    ),
    SettingsDescriptor(
        key="app.version",
        label="Application version",
        source_of_truth="env",
        owner="platform",
        visibility="read_only",
        risk_class="low",
        environment_scope="all",
        restart_required="yes",
        audit_required="no",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:13",
        category="Environment",
        value_reader=lambda: settings.app_version,
    ),
    SettingsDescriptor(
        key="app.env",
        label="Application environment",
        source_of_truth="env",
        owner="infra",
        visibility="read_only",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:14",
        category="Environment",
        value_reader=lambda: settings.app_env,
    ),
    SettingsDescriptor(
        key="api.v1_prefix",
        label="API v1 prefix",
        source_of_truth="env",
        owner="platform",
        visibility="read_only",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:15",
        category="Environment",
        value_reader=lambda: settings.api_v1_prefix,
    ),
    SettingsDescriptor(
        key="database.url",
        label="Database URL",
        source_of_truth="env",
        owner="infra/security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:16",
        category="Security-sensitive values",
        value_reader=lambda: settings.database_url,
    ),
    SettingsDescriptor(
        key="redis.url",
        label="Redis URL",
        source_of_truth="env",
        owner="infra/security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:20",
        category="Security-sensitive values",
        value_reader=lambda: settings.redis_url,
    ),
    SettingsDescriptor(
        key="jwt.secret",
        label="JWT secret",
        source_of_truth="env",
        owner="security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:21",
        category="Security-sensitive values",
        value_reader=lambda: settings.jwt_secret,
    ),
    SettingsDescriptor(
        key="jwt.access_ttl_minutes",
        label="JWT access TTL minutes",
        source_of_truth="env",
        owner="security",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:25",
        category="Security-sensitive values",
        value_reader=lambda: settings.jwt_access_token_ttl_minutes,
    ),
    SettingsDescriptor(
        key="game_launch.token_ttl_minutes",
        label="Game launch token TTL minutes",
        source_of_truth="env",
        owner="security/platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:28",
        category="Security-sensitive values",
        value_reader=lambda: settings.game_launch_token_ttl_minutes,
    ),
    SettingsDescriptor(
        key="game_launch.signing_key",
        label="Game launch signing key",
        source_of_truth="env",
        owner="security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:5.1",
        category="Security-sensitive values",
        status="pending",
        notes=("No separate signing key is implemented yet; launch tokens currently depend on the JWT secret path.",),
    ),
    SettingsDescriptor(
        key="site_access.password",
        label="Site access password",
        source_of_truth="env",
        owner="security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:31",
        category="Security-sensitive values",
        value_reader=lambda: settings.site_access_password,
    ),
    SettingsDescriptor(
        key="site_access.client_default",
        label="Client default site access password",
        source_of_truth="code",
        owner="security",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="frontend/app/ui/player-register-page.tsx",
        category="Security-sensitive values",
        notes=("Closed: registration no longer embeds a default site access password.",),
        value_reader=lambda: "removed",
    ),
    SettingsDescriptor(
        key="mines.server_seed",
        label="Mines server seed",
        source_of_truth="env",
        owner="security/fairness",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:35",
        category="Security-sensitive values",
        value_reader=lambda: settings.mines_server_seed,
    ),
    SettingsDescriptor(
        key="cors.allowed_origins",
        label="CORS allowed origins",
        source_of_truth="env",
        owner="security/infra",
        visibility="masked",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="count_only",
        evidence="backend/app/core/config.py:39",
        category="Environment",
        value_reader=lambda: settings.cors_allowed_origins,
    ),
    SettingsDescriptor(
        key="assets.storage_root",
        label="Asset storage root",
        source_of_truth="env",
        owner="platform/infra",
        visibility="masked",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="partial",
        evidence="backend/app/core/config.py:45",
        category="Environment",
        value_reader=lambda: settings.asset_storage_root,
    ),
    SettingsDescriptor(
        key="assets.public_base_url",
        label="Asset public base URL",
        source_of_truth="env",
        owner="platform",
        visibility="read_only",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:48",
        category="Environment",
        value_reader=lambda: settings.asset_public_base_url,
    ),
    SettingsDescriptor(
        key="access_session.timeout",
        label="Access session timeout",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/access_sessions/service.py:23",
        category="Session/table/recovery policy",
        value_reader=lambda: _format_timedelta_minutes(ACCESS_SESSION_TIMEOUT),
    ),
    SettingsDescriptor(
        key="access_session.sweep_interval",
        label="Access session sweep interval seconds",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/main.py:17",
        category="Session/table/recovery policy",
        value_reader=lambda: "30",
    ),
    SettingsDescriptor(
        key="access_session.sweep_limit",
        label="Access session sweep limit",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/access_sessions/service.py:24",
        category="Session/table/recovery policy",
        value_reader=lambda: ACCESS_SESSION_TIMEOUT_SWEEP_LIMIT,
    ),
    SettingsDescriptor(
        key="table_session.max_chips",
        label="Table session max chips",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/table_sessions/service.py:13",
        category="Session/table/recovery policy",
        value_reader=lambda: str(TABLE_SESSION_MAX_CHIPS),
    ),
    SettingsDescriptor(
        key="table_session.default_chips",
        label="Table session default chips",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/table_sessions/service.py:14",
        category="Session/table/recovery policy",
        value_reader=lambda: str(TABLE_SESSION_DEFAULT_CHIPS),
    ),
    SettingsDescriptor(
        key="demo.token_rate_limit",
        label="Demo token rate limit",
        source_of_truth="code",
        owner="platform/security",
        visibility="editable_future",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/api/routes/demo.py:27",
        category="Security-sensitive values",
        editable_when="After a rate-limit policy and audit trail are approved.",
        value_reader=lambda: "code constant",
    ),
    SettingsDescriptor(
        key="game_registry.backends",
        label="Backend game registry",
        source_of_truth="code",
        owner="platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/game_codes.py:1",
        category="Game registry health",
        value_reader=lambda: ", ".join(ALLOWED_GAME_CODES),
    ),
    SettingsDescriptor(
        key="catalog.publication_flags",
        label="Catalog publication flags",
        source_of_truth="db",
        owner="platform/product",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="no",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/catalog/admin_title_service.py",
        category="Game registry health",
        status="pending",
        notes=("Settings MVP reports the capability, not live DB catalog health.",),
        value_reader=lambda: "catalog/site_titles",
    ),
    SettingsDescriptor(
        key="health.ready_db_redis",
        label="Readiness DB/Redis checks",
        source_of_truth="derived",
        owner="infra",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/api/routes/health.py",
        category="Environment",
        notes=("Closed: /ready checks app, database and Redis.",),
        value_reader=lambda: "app + database + redis",
    ),
    SettingsDescriptor(
        key="auth.rbac_fallback",
        label="Admin RBAC missing-profile fallback",
        source_of_truth="code",
        owner="security",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/api/dependencies.py",
        category="Security-sensitive values",
        notes=("Closed: admin dependencies require explicit admin_profiles rows.",),
        value_reader=lambda: "removed",
    ),
    SettingsDescriptor(
        key="cms_v2_lab.admin_token_in_query",
        label="CMS v2 lab admin token query",
        source_of_truth="code",
        owner="security/platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="local",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="frontend/app/ui/admin-shell-panel.tsx",
        category="Security-sensitive values",
        notes=("Closed: Site v2 lab no longer receives the admin token in the query string.",),
        value_reader=lambda: "removed",
    ),
    SettingsDescriptor(
        key="error_registry.status",
        label="Error registry status",
        source_of_truth="code",
        owner="platform/support",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/api/errors.py:28",
        category="Error Matrix status",
        value_reader=lambda: f"{len(ERROR_REGISTRY)} CK codes",
    ),
    SettingsDescriptor(
        key="frontend.api_base_url",
        label="Frontend API base URL",
        source_of_truth="env",
        owner="infra",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="frontend/app/lib/api.ts:9",
        category="Environment",
        value_reader=lambda: "NEXT_PUBLIC_API_BASE_URL build-time",
    ),
    SettingsDescriptor(
        key="i18n.allowed_locales",
        label="Allowed game locales",
        source_of_truth="code",
        owner="product",
        visibility="read_only",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/games/boxe/i18n_manifest.py",
        category="Environment",
        value_reader=lambda: "it, en, de, es",
    ),
    SettingsDescriptor(
        key="mines.payout_runtime_path",
        label="Mines payout runtime path",
        source_of_truth="code",
        owner="finance",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/games/mines/runtime.py:6",
        category="Finance/replay/retention status",
        value_reader=lambda: "docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json",
    ),
    SettingsDescriptor(
        key="boxe.payout_runtime_path",
        label="BOXE payout runtime path",
        source_of_truth="code",
        owner="finance",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/games/boxe/math.py:9",
        category="Finance/replay/retention status",
        value_reader=lambda: "backend/app/modules/games/boxe/math.py",
    ),
    SettingsDescriptor(
        key="hi_lo.payout_runtime_path",
        label="HI-LO payout runtime path",
        source_of_truth="code",
        owner="finance",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/games/hi_lo/math.py:10",
        category="Finance/replay/retention status",
        value_reader=lambda: "backend/app/modules/games/hi_lo/math.py",
    ),
    SettingsDescriptor(
        key="finance.replay_retention",
        label="Finance replay retention",
        source_of_truth="document",
        owner="finance/legal",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="unknown",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:180",
        category="Finance/replay/retention status",
        value_reader=lambda: "online 30 days; cold storage TBD legal",
    ),
    SettingsDescriptor(
        key="replay.retention_online_days",
        label="Replay retention online days",
        source_of_truth="document",
        owner="finance/legal",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="unknown",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:180",
        category="Finance/replay/retention status",
        value_reader=lambda: "30",
    ),
    SettingsDescriptor(
        key="replay.retention_cold_storage",
        label="Replay retention cold storage",
        source_of_truth="document",
        owner="finance/legal",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="unknown",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:181",
        category="Finance/replay/retention status",
        status="pending",
        notes=("Cold-storage duration is a legal decision, not an MVP runtime setting.",),
        value_reader=lambda: "TBD legal",
    ),
    SettingsDescriptor(
        key="crypto_wallet.enabled",
        label="Crypto wallet enabled",
        source_of_truth="document",
        owner="product",
        visibility="editable_future",
        risk_class="critical",
        environment_scope="production",
        restart_required="unknown",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:5.1",
        category="Finance/replay/retention status",
        status="pending",
        editable_when="After a dedicated production crypto wallet, compliance, ledger and custody plan.",
        value_reader=lambda: "future phase 2 production",
    ),
)


CAPABILITY_MATRIX: tuple[dict[str, str], ...] = (
    {
        "capability": "Descriptor contract",
        "db": "n/a",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "read",
        "player_ui": "n/a",
        "css": "n/a",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Code-backed read-only list with mandatory metadata.",
    },
    {
        "capability": "Backend read model superadmin-only",
        "db": "read admin_profiles",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "consume",
        "player_ui": "n/a",
        "css": "n/a",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Requires explicit admin profile with is_superadmin true.",
    },
    {
        "capability": "Frontend Platform Settings UI",
        "db": "n/a",
        "backend": "consume",
        "api_payload": "parse",
        "admin_ui": "NEW",
        "player_ui": "n/a",
        "css": "NEW",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Working status/risk/visibility filters, expandable explanations, no editable inputs, no save, no publish.",
    },
    {
        "capability": "Game registry health",
        "db": "n/a",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "NEW",
        "player_ui": "n/a",
        "css": "NEW",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Backend game_codes.py is MVP source of truth; adapters can be pending.",
    },
    {
        "capability": "Error Matrix placeholder",
        "db": "n/a",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "NEW",
        "player_ui": "n/a",
        "css": "NEW",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "WP1 registry is present, so CK.* rows are surfaced read-only.",
    },
    {
        "capability": "Descriptor explanations",
        "db": "n/a",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "NEW",
        "player_ui": "n/a",
        "css": "NEW",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Every descriptor has IT/EN operator-readable explanation text.",
    },
    {
        "capability": "Security/settings gap closure",
        "db": "n/a",
        "backend": "UPDATE",
        "api_payload": "UPDATE",
        "admin_ui": "consume",
        "player_ui": "n/a",
        "css": "n/a",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Four CTO-mandated gaps are closed at MVP level and keep long-term follow-up notes.",
    },
)


def build_platform_settings_inventory() -> dict[str, object]:
    validate_descriptor_contract()
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "contract": {
            "required_fields": [
                "key",
                "label",
                "source_of_truth",
                "owner",
                "visibility",
                "risk_class",
                "environment_scope",
                "restart_required",
                "audit_required",
                "editable_now",
                "masking_rule",
                "evidence",
                "explanation",
            ],
            "visibility_values": sorted(VISIBILITIES),
            "masking_rule_values": sorted(MASKING_RULES),
        },
        "summary": _build_summary(),
        "inventory": [_serialize_descriptor(descriptor) for descriptor in SETTINGS_DESCRIPTORS],
        "gap_risks": [_serialize_gap(gap) for gap in GAP_RISKS],
        "game_registry_health": build_game_registry_health(),
        "error_matrix": build_error_matrix(),
        "capability_matrix": list(CAPABILITY_MATRIX),
    }


def validate_descriptor_contract() -> None:
    keys: set[str] = set()
    for descriptor in SETTINGS_DESCRIPTORS:
        if descriptor.key in keys:
            raise ValueError(f"Duplicate platform settings descriptor key: {descriptor.key}")
        keys.add(descriptor.key)

        for field_name in (
            "key",
            "label",
            "source_of_truth",
            "owner",
            "visibility",
            "risk_class",
            "environment_scope",
            "restart_required",
            "audit_required",
            "masking_rule",
            "evidence",
            "category",
        ):
            if not getattr(descriptor, field_name):
                raise ValueError(f"{descriptor.key} is missing required field {field_name}")
        if descriptor.source_of_truth not in SOURCES:
            raise ValueError(f"{descriptor.key} has invalid source_of_truth")
        if descriptor.visibility not in VISIBILITIES:
            raise ValueError(f"{descriptor.key} has invalid visibility")
        if descriptor.risk_class not in RISK_CLASSES:
            raise ValueError(f"{descriptor.key} has invalid risk_class")
        if descriptor.restart_required not in RESTART_VALUES:
            raise ValueError(f"{descriptor.key} has invalid restart_required")
        if descriptor.audit_required not in AUDIT_VALUES:
            raise ValueError(f"{descriptor.key} has invalid audit_required")
        if descriptor.masking_rule not in MASKING_RULES:
            raise ValueError(f"{descriptor.key} has invalid masking_rule")
        if descriptor.status not in STATUSES:
            raise ValueError(f"{descriptor.key} has invalid status")
        if descriptor.editable_now is not False:
            raise ValueError(f"{descriptor.key} must not be editable in the MVP")
        if descriptor.visibility == "editable_future" and not descriptor.editable_when:
            raise ValueError(f"{descriptor.key} is editable_future without editable_when")
        explanation = SETTING_EXPLANATIONS.get(descriptor.key)
        if not explanation or not explanation.get("it") or not explanation.get("en"):
            raise ValueError(f"{descriptor.key} is missing IT/EN explanation")


def build_game_registry_health() -> list[dict[str, object]]:
    return [_build_game_health(game_code) for game_code in ALLOWED_GAME_CODES]


def build_error_matrix() -> dict[str, object]:
    codes = [
        {
            "code": definition.code,
            "http_status": definition.http_status,
            "message": definition.message,
            "retryable": definition.retryable,
            "log_level": definition.log_level,
        }
        for definition in sorted(ERROR_REGISTRY.values(), key=lambda item: item.code)
        if definition.code.startswith("CK.")
    ]
    return {
        "status": "available" if codes else "pending",
        "source": "backend/app/api/errors.py",
        "codes": codes,
        "notes": [] if codes else ["WP1 error registry not detected; placeholder only."],
    }


def _build_summary() -> dict[str, object]:
    total = len(SETTINGS_DESCRIPTORS)
    gaps = sum(1 for descriptor in SETTINGS_DESCRIPTORS if descriptor.status == "gap")
    pending = sum(1 for descriptor in SETTINGS_DESCRIPTORS if descriptor.status == "pending")
    hidden = sum(1 for descriptor in SETTINGS_DESCRIPTORS if descriptor.visibility == "hidden")
    masked = sum(1 for descriptor in SETTINGS_DESCRIPTORS if descriptor.visibility == "masked")
    return {
        "total_descriptors": total,
        "gap_count": gaps,
        "pending_count": pending,
        "hidden_count": hidden,
        "masked_count": masked,
        "editable_now_count": 0,
    }


def _serialize_descriptor(descriptor: SettingsDescriptor) -> dict[str, object]:
    row: dict[str, object] = {
        "key": descriptor.key,
        "label": descriptor.label,
        "source_of_truth": descriptor.source_of_truth,
        "owner": descriptor.owner,
        "visibility": descriptor.visibility,
        "risk_class": descriptor.risk_class,
        "environment_scope": descriptor.environment_scope,
        "restart_required": descriptor.restart_required,
        "audit_required": descriptor.audit_required,
        "editable_now": descriptor.editable_now,
        "masking_rule": descriptor.masking_rule,
        "evidence": descriptor.evidence,
        "category": descriptor.category,
        "status": descriptor.status,
        "state": _build_state(descriptor),
        "notes": list(descriptor.notes),
        "explanation": SETTING_EXPLANATIONS[descriptor.key],
    }
    if descriptor.editable_when:
        row["editable_when"] = descriptor.editable_when
    return row


def _build_state(descriptor: SettingsDescriptor) -> dict[str, object]:
    raw_value = _read_value(descriptor)
    configured = _is_configured(raw_value)
    state: dict[str, object] = {
        "status": descriptor.status,
        "configured": configured,
    }

    if descriptor.visibility == "hidden":
        return state

    if descriptor.visibility == "masked":
        state["display_value"] = _mask_value(raw_value, descriptor.masking_rule)
        return state

    if configured:
        state["display_value"] = _safe_display_value(raw_value)
    else:
        state["display_value"] = "missing"
    return state


def _read_value(descriptor: SettingsDescriptor) -> object | None:
    if descriptor.value_reader is None:
        return None
    return descriptor.value_reader()


def _is_configured(value: object | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (tuple, list, set, dict)):
        return bool(value)
    return True


def _mask_value(value: object | None, masking_rule: str) -> str:
    if not _is_configured(value):
        return "missing"
    if masking_rule == "count_only":
        if isinstance(value, (tuple, list, set)):
            return f"{len(value)} entries configured"
        return "configured"
    if masking_rule == "partial":
        if isinstance(value, Path):
            return f".../{value.name}"
        raw = str(value)
        parsed = urlparse(raw)
        if parsed.hostname:
            return parsed.hostname
        if len(raw) <= 8:
            return "***"
        return f"{raw[:3]}...{raw[-3:]}"
    if masking_rule == "hash_only":
        return "hash hidden"
    return "configured"


def _safe_display_value(value: object | None) -> str:
    if value is None:
        return "missing"
    if isinstance(value, (tuple, list, set)):
        return ", ".join(str(item) for item in value)
    return str(value)


def _format_timedelta_minutes(value: Any) -> str:
    total_seconds = int(value.total_seconds())
    minutes = total_seconds // 60
    return f"{minutes} minutes"


def _serialize_gap(gap: GapRisk) -> dict[str, str]:
    return {
        "key": gap.key,
        "severity": gap.severity,
        "impact": gap.impact,
        "mvp_mitigation": gap.mvp_mitigation,
        "long_term_mitigation": gap.long_term_mitigation,
        "follow_up_wp": gap.follow_up_wp,
        "evidence": gap.evidence,
    }


def _build_game_health(game_code: str) -> dict[str, object]:
    checks = {
        "backend": {
            "status": "present",
            "evidence": "backend/app/modules/platform/game_codes.py",
        },
        "frontend_player_registry": _frontend_registry_check(
            path=REPO_ROOT / "frontend/app/ui/player-game-registry.ts",
            token=f"{game_code}:",
            evidence="frontend/app/ui/player-game-registry.ts",
        ),
        "title_editor_registry": _frontend_registry_check(
            path=REPO_ROOT / "frontend/app/ui/title-editor/engine-editor-registry.ts",
            token=f"{game_code}:",
            evidence="frontend/app/ui/title-editor/engine-editor-registry.ts",
        ),
        "finance_replay_descriptor": _frontend_registry_check(
            path=REPO_ROOT / "frontend/app/ui/game-reporting-registry.tsx",
            token=f"{game_code}:",
            evidence="frontend/app/ui/game-reporting-registry.tsx",
            pending_note="WP3 finance/replay registry not detected in this workspace.",
        ),
        "error_namespace": _error_namespace_check(),
        "smoke_status": {
            "status": "pending",
            "evidence": "manual smoke not tracked by Settings MVP",
            "notes": ["No per-game smoke status feed exists yet."],
        },
    }
    aggregate_status = "present"
    for check in checks.values():
        if check["status"] == "gap":
            aggregate_status = "gap"
            break
        if check["status"] == "pending":
            aggregate_status = "pending"
    return {
        "game_code": game_code,
        "source_of_truth": "backend/app/modules/platform/game_codes.py",
        "status": aggregate_status,
        "checks": checks,
    }


def _frontend_registry_check(
    *,
    path: Path,
    token: str,
    evidence: str,
    pending_note: str = "Adapter file not detected in this workspace.",
) -> dict[str, object]:
    if not path.exists():
        return {
            "status": "pending",
            "evidence": evidence,
            "notes": [pending_note],
        }
    source = path.read_text(encoding="utf-8")
    if token in source:
        return {
            "status": "present",
            "evidence": evidence,
            "notes": [],
        }
    return {
        "status": "gap",
        "evidence": evidence,
        "notes": [f"Missing adapter token {token}."],
    }


def _error_namespace_check() -> dict[str, object]:
    has_game_namespace = any(code.startswith("CK.GAME.") for code in ERROR_REGISTRY)
    if has_game_namespace:
        return {
            "status": "present",
            "evidence": "backend/app/api/errors.py",
            "notes": ["Shared CK.GAME namespace present; game-specific namespaces can be added later."],
        }
    return {
        "status": "pending",
        "evidence": "backend/app/api/errors.py",
        "notes": ["WP1 error namespace not detected."],
    }
