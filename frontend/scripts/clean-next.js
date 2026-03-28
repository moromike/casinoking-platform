const fs = require("fs");
const path = require("path");

const nextDir = path.join(process.cwd(), ".next");

function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function removeEntryWithRetry(targetPath, attempts = 5) {
  for (let index = 0; index < attempts; index += 1) {
    try {
      fs.rmSync(targetPath, { recursive: true, force: true });
      return;
    } catch (error) {
      if (!error || (error.code !== "EBUSY" && error.code !== "EPERM")) {
        throw error;
      }
      if (index === attempts - 1) {
        throw error;
      }
      sleep(75);
    }
  }
}

try {
  if (!fs.existsSync(nextDir)) {
    fs.mkdirSync(nextDir, { recursive: true });
    process.exit(0);
  }

  for (const entry of fs.readdirSync(nextDir)) {
    removeEntryWithRetry(path.join(nextDir, entry));
  }
} catch (error) {
  if (!error || (error.code !== "EBUSY" && error.code !== "EPERM")) {
    throw error;
  }
}
