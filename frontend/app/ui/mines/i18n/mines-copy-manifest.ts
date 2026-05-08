export const MINES_ALLOWED_LOCALES = ["it", "en", "de", "es"] as const;

export type MinesLocaleCode = (typeof MINES_ALLOWED_LOCALES)[number];

export type MinesCopyKey =
  | "game.title"
  | "actions.bet"
  | "actions.bet_loading"
  | "actions.collect"
  | "actions.collect_loading"
  | "actions.exit_aria"
  | "actions.game_info"
  | "actions.back_to_site_aria"
  | "actions.done"
  | "actions.ok"
  | "mode.demo_badge"
  | "round.won_notice"
  | "round.lost_notice"
  | "settings.grid_size"
  | "settings.game_settings"
  | "settings.mines"
  | "settings.mines_count_label"
  | "settings.bet_amount"
  | "balance.demo"
  | "balance.default"
  | "balance.wallet"
  | "balance.table"
  | "balance.win"
  | "balance.zero_chips"
  | "rules.dialog_aria"
  | "rules.header_title"
  | "rules.intro"
  | "rules.close_aria"
  | "rules.ways_to_win"
  | "rules.payout_display"
  | "rules.safe_reveal"
  | "rules.settings_menu"
  | "rules.bet_collect"
  | "format.multiplier_suffix"
  | "format.chip_suffix"
  | "format.cells"
  | "quick_launch.quick_start.label"
  | "quick_launch.quick_start.description"
  | "quick_launch.standard_table.label"
  | "quick_launch.standard_table.description"
  | "quick_launch.high_volatility.label"
  | "quick_launch.high_volatility.description"
  | "launch.choose_table_balance"
  | "launch.balance_source_aria"
  | "launch.real_money"
  | "launch.bonus"
  | "launch.available_balance"
  | "launch.maximum"
  | "launch.table_entry_amount"
  | "launch.entering"
  | "launch.enter_game"
  | "runtime.restoring_title"
  | "runtime.restoring_text"
  | "runtime.demo_closed_text"
  | "runtime.session_expired_title"
  | "runtime.session_expired_text"
  | "runtime.session_expiring_title"
  | "runtime.session_expiring_text"
  | "runtime.session_closed_title"
  | "runtime.session_closed_text"
  | "runtime.reload_required_title"
  | "runtime.reload_required_text"
  | "errors.action_needed"
  | "errors.auth_invalid"
  | "errors.insufficient_balance"
  | "errors.network_start"
  | "errors.network_play"
  | "errors.network_sync"
  | "errors.network_access"
  | "errors.network_load_runtime"
  | "errors.network_start_demo"
  | "errors.network_generic"
  | "errors.start_failed"
  | "errors.action_failed"
  | "errors.update_balance_failed"
  | "errors.resume_failed"
  | "errors.open_table_failed"
  | "errors.operation_failed"
  | "errors.network_suffix"
  | "board.aria.mine"
  | "board.aria.safe"
  | "board.aria.hidden"
  | "board.face.mine"
  | "board.face.safe"
  | "board.face.hidden";

export const MINES_RULE_SECTION_KEYS = [
  "ways_to_win",
  "payout_display",
  "settings_menu",
  "bet_collect",
  "balance_display",
  "general",
  "history",
] as const;

export type MinesRuleSectionKey = (typeof MINES_RULE_SECTION_KEYS)[number];

export type MinesCopyDefinition = {
  key: MinesCopyKey;
  required: boolean;
  maxLength?: number;
  placeholders?: string[];
};

export const MINES_DEFAULT_LOCALE: MinesLocaleCode = "it";
export const MINES_FALLBACK_LOCALE: MinesLocaleCode = "it";

export const MINES_COPY_MANIFEST: readonly MinesCopyDefinition[] = [
  { key: "game.title", required: true, maxLength: 80 },
  { key: "actions.bet", required: true, maxLength: 32 },
  { key: "actions.bet_loading", required: true, maxLength: 32 },
  { key: "actions.collect", required: true, maxLength: 32 },
  { key: "actions.collect_loading", required: true, maxLength: 32 },
  { key: "actions.exit_aria", required: true, maxLength: 80, placeholders: ["gameTitle"] },
  { key: "actions.game_info", required: true, maxLength: 32 },
  { key: "actions.back_to_site_aria", required: true, maxLength: 80 },
  { key: "actions.done", required: true, maxLength: 32 },
  { key: "actions.ok", required: true, maxLength: 32 },
  { key: "mode.demo_badge", required: true, maxLength: 32 },
  { key: "round.won_notice", required: true, maxLength: 160, placeholders: ["amount"] },
  { key: "round.lost_notice", required: true, maxLength: 80 },
  { key: "settings.grid_size", required: true, maxLength: 32 },
  { key: "settings.game_settings", required: true, maxLength: 64 },
  { key: "settings.mines", required: true, maxLength: 32 },
  { key: "settings.mines_count_label", required: true, maxLength: 32, placeholders: ["count"] },
  { key: "settings.bet_amount", required: true, maxLength: 32 },
  { key: "balance.demo", required: true, maxLength: 32 },
  { key: "balance.default", required: true, maxLength: 32 },
  { key: "balance.wallet", required: true, maxLength: 64, placeholders: ["walletType"] },
  { key: "balance.table", required: true, maxLength: 32 },
  { key: "balance.win", required: true, maxLength: 32 },
  { key: "balance.zero_chips", required: true, maxLength: 32 },
  { key: "rules.dialog_aria", required: true, maxLength: 80, placeholders: ["gameTitle"] },
  { key: "rules.header_title", required: true, maxLength: 80, placeholders: ["gameTitle"] },
  { key: "rules.intro", required: true, maxLength: 160 },
  { key: "rules.close_aria", required: true, maxLength: 80 },
  { key: "rules.ways_to_win", required: true, maxLength: 64 },
  { key: "rules.payout_display", required: true, maxLength: 64 },
  { key: "rules.safe_reveal", required: true, maxLength: 64, placeholders: ["step"] },
  { key: "rules.settings_menu", required: true, maxLength: 64 },
  { key: "rules.bet_collect", required: true, maxLength: 64 },
  { key: "format.multiplier_suffix", required: true, maxLength: 8 },
  { key: "format.chip_suffix", required: true, maxLength: 12 },
  { key: "format.cells", required: true, maxLength: 32, placeholders: ["count"] },
  { key: "quick_launch.quick_start.label", required: true, maxLength: 32 },
  { key: "quick_launch.quick_start.description", required: true, maxLength: 120 },
  { key: "quick_launch.standard_table.label", required: true, maxLength: 32 },
  { key: "quick_launch.standard_table.description", required: true, maxLength: 120 },
  { key: "quick_launch.high_volatility.label", required: true, maxLength: 32 },
  { key: "quick_launch.high_volatility.description", required: true, maxLength: 120 },
  { key: "launch.choose_table_balance", required: true, maxLength: 80 },
  { key: "launch.balance_source_aria", required: true, maxLength: 80 },
  { key: "launch.real_money", required: true, maxLength: 32 },
  { key: "launch.bonus", required: true, maxLength: 32 },
  { key: "launch.available_balance", required: true, maxLength: 64 },
  { key: "launch.maximum", required: true, maxLength: 32 },
  { key: "launch.table_entry_amount", required: true, maxLength: 64 },
  { key: "launch.entering", required: true, maxLength: 32 },
  { key: "launch.enter_game", required: true, maxLength: 32 },
  { key: "runtime.restoring_title", required: true, maxLength: 80 },
  { key: "runtime.restoring_text", required: true, maxLength: 180 },
  { key: "runtime.demo_closed_text", required: true, maxLength: 180 },
  { key: "runtime.session_expired_title", required: true, maxLength: 80 },
  { key: "runtime.session_expired_text", required: true, maxLength: 180 },
  { key: "runtime.session_expiring_title", required: true, maxLength: 80 },
  { key: "runtime.session_expiring_text", required: true, maxLength: 180, placeholders: ["seconds"] },
  { key: "runtime.session_closed_title", required: true, maxLength: 80 },
  { key: "runtime.session_closed_text", required: true, maxLength: 180 },
  { key: "runtime.reload_required_title", required: true, maxLength: 80 },
  { key: "runtime.reload_required_text", required: true, maxLength: 180 },
  { key: "errors.action_needed", required: true, maxLength: 80 },
  { key: "errors.auth_invalid", required: true, maxLength: 180 },
  { key: "errors.insufficient_balance", required: true, maxLength: 120 },
  { key: "errors.network_start", required: true, maxLength: 180 },
  { key: "errors.network_play", required: true, maxLength: 180 },
  { key: "errors.network_sync", required: true, maxLength: 180 },
  { key: "errors.network_access", required: true, maxLength: 180 },
  { key: "errors.network_load_runtime", required: true, maxLength: 180 },
  { key: "errors.network_start_demo", required: true, maxLength: 180 },
  { key: "errors.network_generic", required: true, maxLength: 180 },
  { key: "errors.start_failed", required: true, maxLength: 180 },
  { key: "errors.action_failed", required: true, maxLength: 180 },
  { key: "errors.update_balance_failed", required: true, maxLength: 180 },
  { key: "errors.resume_failed", required: true, maxLength: 180 },
  { key: "errors.open_table_failed", required: true, maxLength: 180 },
  { key: "errors.operation_failed", required: true, maxLength: 80 },
  { key: "errors.network_suffix", required: true, maxLength: 120 },
  { key: "board.aria.mine", required: true, maxLength: 80, placeholders: ["cell"] },
  { key: "board.aria.safe", required: true, maxLength: 80, placeholders: ["cell"] },
  { key: "board.aria.hidden", required: true, maxLength: 80, placeholders: ["cell"] },
  { key: "board.face.mine", required: true, maxLength: 32 },
  { key: "board.face.safe", required: true, maxLength: 32 },
  { key: "board.face.hidden", required: true, maxLength: 32 },
] as const;

export const MINES_COPY_KEYS = MINES_COPY_MANIFEST.map((entry) => entry.key);
