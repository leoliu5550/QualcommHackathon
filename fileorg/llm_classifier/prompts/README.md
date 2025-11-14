# LLM Classifier Prompt Templates

This directory contains Jinja2 prompt templates used for file classification, organized by LLM provider and version.

## Version Control Strategy

### How to Manage Versions

1. **Add a New Version**: Create a new version directory (e.g., `v2`, `v3`)

   ```bash
   mkdir -p fileorg/llm_classifier/prompts/llama3b/v2
   cp fileorg/llm_classifier/prompts/llama3b/v1/*.jinja2 fileorg/llm_classifier/prompts/llama3b/v2/
   # Edit the new version templates
   ```

2. **Switch Versions**: Specify the version through parameters in the code

   ```python
   # Use v1
   builder = ClassificationPromptBuilder(loader, provider="llama3b", version="v1")

   # Switch to v2
   builder = ClassificationPromptBuilder(loader, provider="llama3b", version="v2")
   ```

3. **A/B Testing**: Create two builders simultaneously to compare different versions

   ```python
   builder_v1 = ClassificationPromptBuilder(loader, provider="llama3b", version="v1")
   builder_v2 = ClassificationPromptBuilder(loader, provider="llama3b", version="v2")
   ```

### Version Naming Recommendations

* `v1`, `v2`, `v3` – Major versions
* `v1.1`, `v1.2` – Minor updates
* `v1-experiment` – Experimental versions

## Template Files

Templates are organized by task type (classification, summary) with separate system and user prompts.

### classification_system.jinja2

System prompt for file classification tasks.

**Available Variables:**

* `suggested_categories` (List[str]): Suggested classification categories

**Example:**

```jinja2
You are an intelligent file organization assistant.

{% if suggested_categories %}
Suggested categories: {{ suggested_categories | join(", ") }}
{% endif %}
```

### classification_user.jinja2

User prompt for classification tasks containing file data.

**Available Variables:**

* `instruction` (str): Classification instruction
* `file_data` (str): JSON-formatted file data

**Example:**

````jinja2
{{ instruction }}

Files to classify:
```json
{{ file_data }}
````

### summary_system.jinja2

System prompt for file summarization tasks.

### summary_user.jinja2

User prompt for summarization tasks containing file content.

````

## Adding a New LLM Provider

To add support for a new LLM provider (e.g., GPT-4, Claude):

1. **Create a Provider Directory**
   ```bash
   mkdir -p fileorg/llm_classifier/prompts/gpt4/v1
````

2. **Create Template Files**

   ```bash
   touch fileorg/llm_classifier/prompts/gpt4/v1/system.jinja2
   touch fileorg/llm_classifier/prompts/gpt4/v1/user.jinja2
   ```

3. **Implement the Corresponding PromptBuilder** (if the format differs)

   ```python
   class GPT4PromptBuilder(IPromptBuilder):
       def build_prompt(self, text: str, instruction: str, max_tokens: int = 150000):
           # Implement GPT-4 specific formatting
           pass
   ```

## Prompt Format

Templates should provide plain text content. Model-specific formatting (such as special tokens)
is handled by the respective PromptBuilder implementations.

## Best Practices

1. **Keep Templates Simple**: Avoid excessive logic in templates.
2. **Use Comments**: Use `{# comment #}` in Jinja2 to explain complex logic.
3. **Test New Versions**: After adding a new version, run unit tests to ensure format correctness.
4. **Maintain a Changelog**: Record all version changes in `CHANGELOG.md`.
5. **Ensure Backward Compatibility**: Keep older versions functional and avoid breaking changes.