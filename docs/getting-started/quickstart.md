# Quick Start Guide

Get started with FileOrg in under 5 minutes! This guide will walk you through your first file organization.

## Your First Organization

### Step 1: Choose Your Target Folder

Pick a messy folder that needs organizing. Common choices:

- `~/Downloads` - Everyone's digital junk drawer
- `~/Documents` - Years of accumulated files
- `~/Desktop` - The infamous cluttered desktop

### Step 2: Preview Mode (Recommended First)

Always start with preview mode to see what FileOrg will do:

```bash
fileorg ~/Downloads --preview
```

This will:
- Scan all files
- Analyze content with AI
- Show proposed organization
- NOT move any files

### Step 3: Review the Plan

FileOrg will display:

```
Organization Preview
========================
Files Found: 156
Proposed Folders: 12

Academic_Research (23 files)
   ├── machine_learning_paper.pdf
   ├── thesis_draft_v3.docx
   └── ...

Financial_Documents (15 files)
   ├── invoice_2024.pdf
   ├── tax_return.xlsx
   └── ...

Personal_Photos (45 files)
   ├── vacation_2024.jpg
   ├── family_reunion.png
   └── ...
```

### Step 4: Execute Organization

Happy with the preview? Run the actual organization:

```bash
fileorg ~/Downloads
```

FileOrg will:
1. Create a backup (`.backup/` folder)
2. Move files to organized folders
3. Generate reports
4. Display summary

## Interactive GUI Mode

Prefer a visual interface? Use GUI mode:

```bash
fileorg start
```

Navigate with arrow keys:
- ↑/↓ - Navigate options
- Enter - Select
- ESC - Go back

## Common Workflows

### Organizing Downloads Folder

```bash
# Preview first
fileorg ~/Downloads --preview

# If satisfied, organize
fileorg ~/Downloads

# Check the report
cat ~/Downloads/.tidy_report/*/organize_report.md
```

### Organizing Project Files

```bash
# For a specific project folder
fileorg /path/to/project --preview

# Organize with custom output
fileorg /path/to/project --output /path/to/organized
```

### Batch Organization

```bash
# Organize multiple folders
for folder in ~/Downloads ~/Desktop ~/Documents; do
    fileorg "$folder" --preview
    read -p "Organize $folder? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        fileorg "$folder"
    fi
done
```

## Restore Original Structure

Changed your mind? Restore is one command away:

```bash
fileorg ~/Downloads --restore
```

This will:
- Read backup data
- Move files back to original locations
- Clean up empty folders
- Preserve all file metadata

## Understanding Reports

After organization, check the reports:

### Tree Structure Report
```bash
# View folder hierarchy
cat ~/Downloads/.tidy_report/*/tree_structure.txt
```

### Statistics Report
```bash
# View organization statistics
cat ~/Downloads/.tidy_report/*/statistics.txt
```

Shows:
- Total files organized
- Folder distribution
- File type breakdown
- Largest/smallest folders

### Markdown Report
```bash
# Comprehensive report with summaries
cat ~/Downloads/.tidy_report/*/organize_report.md
```

## Configuration Tips

### Use Faster Models

For quicker processing on CPU:

```python
# config.json
{
  "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "backend": "local"
}
```

### Limit File Types

Focus on specific file types:

```bash
# Only organize documents
fileorg ~/Downloads --types "pdf,docx,txt"
```

### Adjust AI Behavior

```python
# More conservative categorization
{
  "temperature": 0.1,
  "use_few_shot": true
}
```

## Best Practices

### 1. Always Preview First
Never run organization without preview, especially on important folders.

### 2. Start Small
Begin with a test folder before organizing your entire system.

### 3. Check Reports
Review the generated reports to understand the organization logic.

### 4. Keep Backups
FileOrg creates automatic backups, but having external backups is wise.

### 5. Custom Categories
For specialized needs, consider training custom models or adjusting prompts.

## Example Scenarios

### Scenario 1: Student's Semester Files

```bash
# Organize semester materials
fileorg ~/University/Fall2024 --preview

# Results in:
# Assignments
# Lecture_Notes  
# Research_Papers
# Lab_Reports
# Exams
```

### Scenario 2: Photographer's Portfolio

```bash
# Organize photo collection
fileorg ~/Photos/Unsorted --preview

# Results in:
# Landscapes
# Portraits
# Events
# Architecture
# Wildlife
```

### Scenario 3: Developer's Projects

```bash
# Organize code projects
fileorg ~/Code/misc --preview

# Results in:
# Python_Projects
# Web_Development
# Documentation
# Scripts_Utils
# Config_Files
```

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "No files found" | Check folder path and permissions |
| "Out of memory" | Use smaller model or process in batches |
| "Slow processing" | Enable GPU or use lighter model |
| "Wrong categorization" | Adjust prompts or use few-shot examples |

## Success Tips

1. **Regular Maintenance**: Run FileOrg weekly on Downloads
2. **Project Organization**: Use for each completed project
3. **Archive Management**: Organize before backing up
4. **Team Sharing**: Generate reports for documentation

## Next Steps

Now that you've organized your first folder:

- Learn about [CLI Usage](../user-guide/cli.md)
- Explore the [API Reference](../api/index.md)

---

**Ready for more?** Check out our [complete user guide](../user-guide/cli.md) for advanced features!