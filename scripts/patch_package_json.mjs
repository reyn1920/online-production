// path: scripts/patch_package_json.mjs
// Add-only merge for Puppeteer scripts/devDependencies.
import fs from "fs";

const PATCH = {
  scripts: {
    "pupp:check": "node tools/puppeteer/check.js",
    "pupp:login": "node tools/puppeteer/login_flow.js",
    "pupp:shot": "node tools/puppeteer/screenshot_check.js",
    "pupp:devices": "node tools/puppeteer/device_matrix.js",
    "pupp:trace": "node tools/puppeteer/trace_run.js",
    "pupp:open:chatgpt": "node tools/puppeteer/open_chatgpt.js",
    "pupp:open:gemini": "node tools/puppeteer/open_gemini.js",
    "pupp:open:abacus": "node tools/puppeteer/open_abacus.js"
  },
  devDependencies: {
    "dotenv": "^16.4.5",
    "pixelmatch": "^5.3.0",
    "pngjs": "^7.0.0"
  }
};

function mergeAddOnly(base, patch) {
  for (const [k, v] of Object.entries(patch)) {
    if (typeof v === "object" && v && !Array.isArray(v)) {
      base[k] = base[k] || {};
      for (const [sk, sv] of Object.entries(v)) {
        if (!(sk in base[k])) base[k][sk] = sv;
      }
    } else {
      if (!(k in base)) base[k] = v;
    }
  }
}

const pathPkg = "./package.json";
if (!fs.existsSync(pathPkg)) {
  console.error("[patch] package.json not found in CWD");
  process.exit(2);
}
const pkg = JSON.parse(fs.readFileSync(pathPkg, "utf8"));
mergeAddOnly(pkg, PATCH);
fs.writeFileSync(pathPkg, JSON.stringify(pkg, null, 2));
console.log("[patch] package.json patched add-only");
