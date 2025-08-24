Restore System
==============

The restore module ensures that any organization can be completely undone, reflecting
our commitment to user control and data safety.

.. automodule:: fileorg.restore.restore_folder
   :members:
   :undoc-members:
   :show-inheritance:

Safety Philosophy
-----------------

We believe users should feel confident about trying FileOrg because they know they
can always go back to exactly where they started.

Features:

- **Complete Reversibility**: Every file returns to its exact original location
- **Cross-Platform Support**: Works with Windows, Linux, and macOS paths
- **Verification**: Confirms successful restoration with detailed reporting
- **Cleanup**: Removes empty folders created during organization

Restore Process
---------------

1. **Backup Validation**: Verify backup file integrity
2. **Path Resolution**: Handle cross-platform path differences
3. **File Movement**: Safely move files to original locations
4. **Directory Cleanup**: Remove empty organization folders
5. **Verification**: Confirm successful restoration

Usage Example
-------------

.. code-block:: bash

   # Restore files to original locations
   fileorg /path/to/organized/folder --restore

The restore process is completely automated and handles edge cases gracefully.

Technical Details
-----------------

- Backup files are stored in `.backup/file_paths.json`
- Cross-platform path normalization ensures compatibility
- Atomic operations minimize risk of partial restoration
- Detailed logging for troubleshooting

Future Enhancements
------------------

We're working on:

- Partial restore capabilities
- Time-based restore points
- Cloud backup integration
- Conflict resolution improvements