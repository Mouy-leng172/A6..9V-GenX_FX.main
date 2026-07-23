// merge-json.js
// Auto-merge VSCode configs + Docker configs into one unified file

const fs = require("fs");
const path = require("path");

const vscodeDir = path.join(__dirname, ".vscode");
const outputFile = path.join(vscodeDir, "merged.launch.json");

// Collect JSON files in .vscode
const jsonFiles = fs.readdirSync(vscodeDir).filter(f => f.endsWith(".json"));

let merged = {
  version: "0.2.0",
  configurations: [],
  docker: {
    dockerfiles: [],
    composeFiles: []
  }
};

// Merge JSON configs
jsonFiles.forEach(file => {
  const filePath = path.join(vscodeDir, file);
  try {
    const content = JSON.parse(fs.readFileSync(filePath, "utf8"));

    if (content.configurations && Array.isArray(content.configurations)) {
      merged.configurations.push(...content.configurations);
    }
    if (file === "settings.json") {
      merged.settings = content;
    }
    if (file === "extensions.json") {
      merged.extensions = content;
    }
  } catch (err) {
    console.error(`Error parsing ${file}:`, err);
  }
});

// Detect Dockerfiles + docker-compose files
const rootFiles = fs.readdirSync(__dirname);
rootFiles.forEach(file => {
  if (file.toLowerCase().startsWith("dockerfile")) {
    merged.docker.dockerfiles.push(file);
  }
  if (file.toLowerCase().startsWith("docker-compose")) {
    merged.docker.composeFiles.push(file);
  }
});

// Write merged file
fs.writeFileSync(outputFile, JSON.stringify(merged, null, 2));
console.log(`Merged configs + Docker references into ${outputFile}`);
