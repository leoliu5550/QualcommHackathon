FileOrg - AI-Powered File Organization
====================================

Welcome to FileOrg's documentation. FileOrg is an intelligent file organization system that uses AI to analyze document content and automatically organize files into meaningful folders.

Our Vision
----------

We're working towards making file organization as intuitive as possible, learning from each interaction to better understand how humans naturally categorize information. Our approach combines traditional file management with cutting-edge AI to understand not just what files are, but what they mean in context.

Quick Start
-----------

.. code-block:: bash

   # Install FileOrg
   pip install fileorg

   # Preview organization without moving files
   fileorg /path/to/directory --preview

   # Organize files
   fileorg /path/to/directory

   # Restore original structure
   fileorg /path/to/directory --restore

Features
--------

- **Content-Based Organization**: Analyzes actual file content, not just filenames
- **AI-Powered Categorization**: Uses LLMs to create meaningful folder names
- **Smart Grouping**: Prevents redundant folders by intelligently grouping similar categories
- **Preview Mode**: See proposed changes before applying them
- **Full Restore**: Complete backup and restore functionality
- **Cross-Platform**: Works seamlessly on Windows, Linux, and macOS
- **NPU Support**: Optimized for Qualcomm Snapdragon processors

API Documentation
=================

Core Modules
------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/cli
   modules/core
   modules/ai
   modules/scanner
   modules/classifier
   modules/parsers
   modules/reporter
   modules/restore

Command Line Interface
----------------------

.. automodule:: fileorg.cli
   :members:

Core Orchestration
------------------

.. automodule:: fileorg.core.organizer
   :members:

AI Interface
------------

.. automodule:: fileorg.ai.interface
   :members:

File Scanner
------------

.. automodule:: fileorg.scanner.core
   :members:

Content Classifier
------------------

.. automodule:: fileorg.classifier.classifier
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`