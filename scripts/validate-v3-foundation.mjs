import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const required = [
  "apps/web/package.json",
  "apps/web/next.config.mjs",
  "apps/web/app/page.tsx",
  "apps/api/main.py",
  "apps/api/requirements.txt",
];

const missing = required.filter((path) => !existsSync(join(root, path)));
if (missing.length > 0) {
  console.error("Foundation validation failed. Missing required runtime files:");
  for (const path of missing) console.error(`- ${path}`);
  process.exit(1);
}

const web = JSON.parse(readFileSync(join(root, "apps/web/package.json"), "utf8"));
for (const script of ["dev", "build", "start"]) {
  if (!web.scripts?.[script]) {
    console.error(`Foundation validation failed. Web script missing: ${script}`);
    process.exit(1);
  }
}

const apiSource = readFileSync(join(root, "apps/api/main.py"), "utf8");
for (const marker of ["FastAPI(", '@app.get("/health")']) {
  if (!apiSource.includes(marker)) {
    console.error(`Foundation validation failed. API marker missing: ${marker}`);
    process.exit(1);
  }
}

console.log("Foundation validation passed: web and API runtime surfaces are present.");
console.log("Worker status: deferred; no implementation is claimed by this baseline.");
