import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import ts from "typescript";

const frontendRoot = path.resolve(import.meta.dirname, "..");

function compileModule(sourcePath, replacements = []) {
  let source = fs.readFileSync(sourcePath, "utf8");
  for (const [from, to] of replacements) {
    source = source.replace(from, to);
  }
  return ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
}

function loadModule(compiledSource, dependencies = {}) {
  const module = { exports: {} };
  vm.runInNewContext(compiledSource, {
    module,
    exports: module.exports,
    process: { env: {} },
    require: (specifier) => {
      if (!(specifier in dependencies)) {
        throw new Error(`Unexpected dependency: ${specifier}`);
      }
      return dependencies[specifier];
    },
  });
  return module.exports;
}

const api = loadModule(compileModule(path.join(frontendRoot, "app/lib/api.ts")));
const adapter = loadModule(
  compileModule(
    path.join(frontendRoot, "app/ui/game-runtime/game-error-copy-adapter.ts"),
    [["@/app/lib/api", "./api"]],
  ),
  { "./api": api },
);

const insufficientBalance = new api.ApiRequestError(
  "Saldo insufficiente.",
  "INSUFFICIENT_BALANCE",
  422,
  { retryable: false },
);

assert.equal(adapter.classifyGameError(insufficientBalance), "insufficient_balance");
