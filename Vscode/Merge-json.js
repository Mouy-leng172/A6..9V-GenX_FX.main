// merge-json.js
// Auto-merge all JSON files in .vscode into one unified file

const fs = require("fs");
const path = require("path");

const vscodeDir = path.join(__dirname, ".vscode");
const outputFile = path.join(vscodeDir, "merged.launch.json");

// Collect all JSON files in .vscode
const files = fs.readdirSync(vscodeDir).filter(f => f.endsWith(".json"));

let merged = {
  version: "0.2.0",
  configurations: []
};

files.forEach(file => {
  const filePath = path.join(vscodeDir, file);
  try
