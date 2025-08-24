File Scanner
============

The scanner module provides intelligent file system scanning capabilities that form the
foundation of our organization pipeline.

.. automodule:: fileorg.scanner.core
   :members:
   :undoc-members:
   :show-inheritance:

Smart Scanning
--------------

Our scanner is designed to be:

- **Respectful**: Minimal system resource usage
- **Intelligent**: Automatic system file exclusion
- **Comprehensive**: Thorough user content discovery
- **Safe**: Graceful permission error handling

Ignored Patterns
----------------

We automatically skip:

- System directories (`.git`, `node_modules`, etc.)
- Hidden files and folders
- Build artifacts and temporary files
- OS-specific system folders

Configuration
-------------

.. code-block:: python

   from fileorg.scanner import FileScanner
   
   # Basic scanning
   scanner = FileScanner('/path/to/directory')
   files = scanner.scan_directory()
   
   # With depth limit
   scanner = FileScanner('/path/to/directory', max_depth=3)
   results = scanner.scan_with_details()

Future Enhancements
------------------

We're working on:

- Real-time change detection
- Cloud storage integration
- Custom ignore pattern support
- Performance optimization for massive directories