export type RegistrationFormConfig = {
  accessCodeLabel: string;
  authenticatedMessage: string;
  authenticatedStatus: string;
  backLabel: string;
  body: string;
  busyLabel: string;
  checkingMessage: string;
  continueLabel: string;
  documentBackLabel: string;
  documentFrontLabel: string;
  documentUploadNote: string;
  emailLabel: string;
  eyebrow: string;
  firstNameLabel: string;
  fiscalCodeLabel: string;
  headline: string;
  lastNameLabel: string;
  legalNoteHtml: string;
  lobbyLabel: string;
  loginLabel: string;
  passwordLabel: string;
  phoneNumberLabel: string;
  postRegisterPath: string;
  requireDocumentImages: boolean;
  showFirstName: boolean;
  showFiscalCode: boolean;
  showLastName: boolean;
  showPhoneNumber: boolean;
  submitLabel: string;
  successMessage: string;
};

export const DEFAULT_REGISTRATION_FORM_CONFIG: RegistrationFormConfig = {
  accessCodeLabel: "Access code",
  authenticatedMessage: "You are already signed in. Opening your account.",
  authenticatedStatus: "Registration is available only before signing in.",
  backLabel: "Back",
  body: "Crea il tuo account player.",
  busyLabel: "Completing...",
  checkingMessage: "Checking current player session.",
  continueLabel: "Continue",
  documentBackLabel: "Document back",
  documentFrontLabel: "Document front",
  documentUploadNote:
    "Document images: PNG, JPEG, or WebP recommended, max 5 MB per side. Recommended 1600 x 1000 px or 1000 x 1600 px, matching document orientation. They are not rendered or resized yet; the backend does not store document files.",
  emailLabel: "Email",
  eyebrow: "Player",
  firstNameLabel: "First name",
  fiscalCodeLabel: "Fiscal code",
  headline: "Registration",
  lastNameLabel: "Last name",
  legalNoteHtml: "",
  lobbyLabel: "Back to lobby",
  loginLabel: "Sign in",
  passwordLabel: "Password",
  phoneNumberLabel: "Phone number",
  postRegisterPath: "/account",
  requireDocumentImages: true,
  showFirstName: true,
  showFiscalCode: true,
  showLastName: true,
  showPhoneNumber: true,
  submitLabel: "Complete registration",
  successMessage: "Registration completed. Your document images will be requested again when backend upload is enabled.",
};

export function readRegistrationFormConfig(
  config: Record<string, unknown> | null | undefined,
): RegistrationFormConfig {
  const source = config ?? {};
  return {
    accessCodeLabel: readString(source.access_code_label, DEFAULT_REGISTRATION_FORM_CONFIG.accessCodeLabel),
    authenticatedMessage: readString(source.authenticated_message, DEFAULT_REGISTRATION_FORM_CONFIG.authenticatedMessage),
    authenticatedStatus: readString(source.authenticated_status, DEFAULT_REGISTRATION_FORM_CONFIG.authenticatedStatus),
    backLabel: readString(source.back_label, DEFAULT_REGISTRATION_FORM_CONFIG.backLabel),
    body: readString(source.body, DEFAULT_REGISTRATION_FORM_CONFIG.body),
    busyLabel: readString(source.busy_label, DEFAULT_REGISTRATION_FORM_CONFIG.busyLabel),
    checkingMessage: readString(source.checking_message, DEFAULT_REGISTRATION_FORM_CONFIG.checkingMessage),
    continueLabel: readString(source.continue_label, DEFAULT_REGISTRATION_FORM_CONFIG.continueLabel),
    documentBackLabel: readString(source.document_back_label, DEFAULT_REGISTRATION_FORM_CONFIG.documentBackLabel),
    documentFrontLabel: readString(source.document_front_label, DEFAULT_REGISTRATION_FORM_CONFIG.documentFrontLabel),
    documentUploadNote: readString(source.document_upload_note, DEFAULT_REGISTRATION_FORM_CONFIG.documentUploadNote),
    emailLabel: readString(source.email_label, DEFAULT_REGISTRATION_FORM_CONFIG.emailLabel),
    eyebrow: readString(source.eyebrow, DEFAULT_REGISTRATION_FORM_CONFIG.eyebrow),
    firstNameLabel: readString(source.first_name_label, DEFAULT_REGISTRATION_FORM_CONFIG.firstNameLabel),
    fiscalCodeLabel: readString(source.fiscal_code_label, DEFAULT_REGISTRATION_FORM_CONFIG.fiscalCodeLabel),
    headline: readString(source.headline, DEFAULT_REGISTRATION_FORM_CONFIG.headline),
    lastNameLabel: readString(source.last_name_label, DEFAULT_REGISTRATION_FORM_CONFIG.lastNameLabel),
    legalNoteHtml: readString(source.legal_note_html, DEFAULT_REGISTRATION_FORM_CONFIG.legalNoteHtml),
    lobbyLabel: readString(source.lobby_label, DEFAULT_REGISTRATION_FORM_CONFIG.lobbyLabel),
    loginLabel: readString(source.login_label, DEFAULT_REGISTRATION_FORM_CONFIG.loginLabel),
    passwordLabel: readString(source.password_label, DEFAULT_REGISTRATION_FORM_CONFIG.passwordLabel),
    phoneNumberLabel: readString(source.phone_number_label, DEFAULT_REGISTRATION_FORM_CONFIG.phoneNumberLabel),
    postRegisterPath: readPostRegisterPath(source.post_register_path),
    requireDocumentImages: readBoolean(
      source.require_document_images,
      DEFAULT_REGISTRATION_FORM_CONFIG.requireDocumentImages,
    ),
    showFirstName: readBoolean(source.show_first_name, DEFAULT_REGISTRATION_FORM_CONFIG.showFirstName),
    showFiscalCode: readBoolean(source.show_fiscal_code, DEFAULT_REGISTRATION_FORM_CONFIG.showFiscalCode),
    showLastName: readBoolean(source.show_last_name, DEFAULT_REGISTRATION_FORM_CONFIG.showLastName),
    showPhoneNumber: readBoolean(source.show_phone_number, DEFAULT_REGISTRATION_FORM_CONFIG.showPhoneNumber),
    submitLabel: readString(source.submit_label, DEFAULT_REGISTRATION_FORM_CONFIG.submitLabel),
    successMessage: readString(source.success_message, DEFAULT_REGISTRATION_FORM_CONFIG.successMessage),
  };
}

function readString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function readBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function readPostRegisterPath(value: unknown): string {
  const rawValue = readString(value, DEFAULT_REGISTRATION_FORM_CONFIG.postRegisterPath);
  if (!rawValue.startsWith("/") || rawValue.startsWith("//")) {
    return DEFAULT_REGISTRATION_FORM_CONFIG.postRegisterPath;
  }
  return rawValue;
}
