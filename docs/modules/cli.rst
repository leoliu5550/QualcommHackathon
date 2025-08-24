Command Line Interface
======================

The FileOrg CLI provides a simple yet powerful interface for intelligent file organization.
We've designed this to be the simplest possible interface to powerful AI-driven file organization.

.. automodule:: fileorg.cli
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

   # Preview organization (recommended first step)
   fileorg /path/to/messy/folder --preview

   # Organize files
   fileorg /path/to/messy/folder

   # Restore original structure
   fileorg /path/to/organized/folder --restore

Advanced Usage
~~~~~~~~~~~~~~

.. code-block:: bash

   # Organize with absolute paths (cross-platform)
   fileorg "C:\Users\Documents\Messy Folder" --preview
   fileorg "/home/user/documents/unsorted" --preview
   fileorg "/Users/user/Desktop/files" --preview

Safety Features
---------------

- **Automatic Backups**: Always creates backups before moving files
- **Preview Mode**: See proposed changes before committing
- **Full Restore**: Complete undo capability
- **Cross-Platform Paths**: Handles Windows, Linux, and macOS paths seamlessly