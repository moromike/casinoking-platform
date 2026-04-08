const fs = require("fs");
const path = require("path");

const root = process.cwd();
const nextDir = path.join(root, ".next");
const nodeModulesCache = path.join(root, "node_modules", ".cache");
const tsBuildInfo = path.join(root, "tsconfig.tsbuildinfo");

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

function cleanDirectory(dirPath) {
  if (!fs.existsSync(dirPath)) {
    return 0;
  }
  let count = 0;
  for (const entry of fs.readdirSync(dirPath)) {
    removeEntryWithRetry(path.join(dirPath, entry));
    count += 1;
  }
  return count;
}

try {
  // 1. Clean .next build cache
  const nextCount = cleanDirectory(nextDir);
  if (!fs.existsSync(nextDir)) {
    fs.mkdirSync(nextDir, { recursive: true });
  }
  console.log(`.next: removed ${nextCount} entries`);

  // 2. Clean node_modules/.cache (webpack/swc/turbopack caches)
  if (fs.existsSync(nodeModulesCache)) {
    removeEntryWithRetry(nodeModulesCache);
    console.log("node_modules/.cache: removed");
  } else {
    console.log("node_modules/.cache: not present");
  }

  // 3. Clean tsconfig.tsbuildinfo (TypeScript incremental build info)
  if (fs.existsSync(tsBuildInfo)) {
    fs.rmSync(tsBuildInfo, { force: true });
    console.log("tsconfig.tsbuildinfo: removed");
  } else {
    console.log("tsconfig.tsbuildinfo: not present");
  }

  console.log("Clean complete.");
} catch (error) {
  if (!error || (error.code !== "EBUSY" && error.code !== "EPERM")) {
    throw error;
  }
  console.warn("Warning: some files were locked and could not be removed.");
}
