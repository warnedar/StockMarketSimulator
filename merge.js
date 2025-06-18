#!/usr/bin/env node
/**
 * merge.js
 *
 * This script traverses a directory tree starting from a specified root and concatenates the content
 * of all files that match the allowed file extensions. It allows you to filter which folders (or files
 * within them) to include or exclude using command-line parameters.
 *
 * Usage (from the command line):
 *   node merge.js --root "./" --output "merged.txt" --include "src,lib" --exclude "node_modules,dist,.git" --ext ".js,.ts,.py"
 *
 * All parameters are optional:
 *   --root:   The root directory to start the traversal (default: current working directory).
 *   --output: The output file path (default: merged_output.txt).
 *   --include: A comma-separated list of folder names (relative to the root) to include.
 *              Only files inside these folders (or their subfolders) will be merged.
 *              If not provided, all folders (except those excluded) are processed.
 *   --exclude: A comma-separated list of folder names (relative to the root) to exclude.
 *              These folders (and their subfolders) will be skipped.
 *   --ext:    A comma-separated list of file extensions to merge (default: common code extensions).
 */

const fs = require('fs');
const path = require('path');

// Simple command-line argument parser
const args = process.argv.slice(2);
function getArgValue(flag) {
  const index = args.indexOf(flag);
  if (index !== -1 && index + 1 < args.length) {
    return args[index + 1];
  }
  return null;
}

// Parse command-line options (or use defaults)
const rootDir = getArgValue('--root') || process.cwd();
const outputFile = getArgValue('--output') || 'merged_output.txt';

const includeFoldersArg = getArgValue('--include'); // comma-separated, e.g., "src,lib"
const excludeFoldersArg = getArgValue('--exclude'); // comma-separated, e.g., "node_modules,dist,.git"
const extArg = getArgValue('--ext'); // comma-separated file extensions, e.g., ".js,.ts,.py"

// Convert comma-separated arguments into arrays (trim spaces)
const includeFolders = includeFoldersArg
  ? includeFoldersArg.split(',').map((s) => s.trim()).filter((s) => s)
  : []; // If empty, include all (except excluded)
const excludeFolders = excludeFoldersArg
  ? excludeFoldersArg.split(',').map((s) => s.trim()).filter((s) => s)
  : ['node_modules', 'dist', '.git']; // Default common excludes

let allowedExtensions = extArg
  ? extArg.split(',').map((s) => s.trim()).filter((s) => s)
  : [
      '.js',
      '.ts',
      '.jsx',
      '.tsx',
      '.py',
      '.java',
      '.cpp',
      '.c',
      '.cs',
      '.rb',
      '.go',
      '.php',
      '.html',
      '.css',
      '.json'
    ]; // Default code file extensions

// This will hold the merged content.
let mergedContent = '';

// Helper: Check if a file (by its full path) is in one of the included folders.
// If no includeFolders are specified, allow all files.
function isInIncludedFolder(filePath) {
  if (includeFolders.length === 0) return true;
  const relativeFilePath = path.relative(rootDir, filePath);
  // Check if the relative path starts with any of the specified include folders.
  return includeFolders.some((folder) => {
    // For example, if folder is "src", then "src/file.js" or "src/sub/file.js" should match.
    return (
      relativeFilePath === folder ||
      relativeFilePath.startsWith(folder + path.sep)
    );
  });
}

// Recursively traverse directories and process files.
function traverseDirectory(dir) {
  let items;
  try {
    items = fs.readdirSync(dir);
  } catch (err) {
    console.error(`Error reading directory ${dir}: ${err}`);
    return;
  }

  for (const item of items) {
    const fullPath = path.join(dir, item);
    let stat;
    try {
      stat = fs.statSync(fullPath);
    } catch (err) {
      console.error(`Error stating file ${fullPath}: ${err}`);
      continue;
    }

    if (stat.isDirectory()) {
      // Check if this directory should be excluded.
      const relativeDir = path.relative(rootDir, fullPath);
      if (excludeFolders.some((ex) => {
          // Exclude if the directory name exactly matches or if it starts with the exclude folder name plus a separator.
          return (
            relativeDir === ex ||
            relativeDir.startsWith(ex + path.sep)
          );
        })) {
        console.log(`Excluding folder: ${fullPath}`);
        continue;
      }
      // Recursively process the subdirectory.
      traverseDirectory(fullPath);
    } else if (stat.isFile()) {
      // Process only files with allowed extensions.
      const fileExt = path.extname(item);
      if (!allowedExtensions.includes(fileExt)) {
        continue;
      }

      // If includeFolders filter is set, check if the file's path is within one of those folders.
      if (!isInIncludedFolder(fullPath)) {
        continue;
      }

      // Read and append the file content.
      console.log(`Adding file: ${fullPath}`);
      let fileContent;
      try {
        fileContent = fs.readFileSync(fullPath, 'utf8');
      } catch (err) {
        console.error(`Error reading file ${fullPath}: ${err}`);
        continue;
      }
      // Add a header and footer to delineate file content.
      mergedContent += `\n// --------- File: ${fullPath} ---------\n`;
      mergedContent += fileContent;
      mergedContent += `\n// --------- End of File: ${fullPath} ---------\n\n`;
    }
  }
}

// Start traversal from the root directory.
traverseDirectory(rootDir);

// Write the merged content into the output file.
try {
  fs.writeFileSync(outputFile, mergedContent, 'utf8');
  console.log(`\nMerged file created at: ${outputFile}`);
} catch (err) {
  console.error(`Error writing to output file ${outputFile}: ${err}`);
}
