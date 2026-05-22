export const BOXE_TABLE_BALANCE_CONFIG = {
  defaultEntryAmount: "0",
  quickAmounts: ["25", "50", "100"],
  walletSources: ["cash", "bonus"] as const,
};

export type BoxeWalletSource = (typeof BOXE_TABLE_BALANCE_CONFIG.walletSources)[number];
