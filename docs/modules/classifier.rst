Content Classifier
==================

This module represents the heart of our AI-driven organization approach. We believe that
understanding content context, not just file types or names, is key to creating truly
helpful organization structures.

.. automodule:: fileorg.classifier.classifier
   :members:
   :undoc-members:
   :show-inheritance:

Intelligent Classification
-------------------------

Our classification system:

- **Semantic Analysis**: Understands content meaning, not just keywords
- **Context Awareness**: Considers relationships between files
- **Smart Grouping**: Prevents folder proliferation
- **Adaptive Learning**: Improves through usage patterns

Classification Process
---------------------

1. **Content Analysis**: Extract semantic meaning from file content
2. **Category Generation**: Create contextually appropriate folder names
3. **Similarity Detection**: Group related categories together
4. **Structure Optimization**: Balance granularity with usability

Example Usage
-------------

.. code-block:: python

   from fileorg.classifier.classifier import create_name
   
   # Process file summaries into organized structure
   summaries = {
       'summaries': [
           {'summary': 'Machine learning research paper', 'path': '/docs/ml.pdf'},
           {'summary': 'Deep learning tutorial', 'path': '/docs/tutorial.pdf'}
       ]
   }
   
   result = create_name.process_files(summaries, '/organized/')

Philosophy
----------

We see this as more than just file moving - it's about creating structures that enhance
human productivity and reduce information chaos. Every decision prioritizes user
experience and cognitive load reduction.