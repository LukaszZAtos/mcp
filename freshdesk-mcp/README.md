# Freshdesk MCP Server

A local MCP (Model Context Protocol) server that connects Claude Desktop to Freshdesk via API key. Runs entirely on your machine — no traffic passes through Anthropic servers.

## Requirements

- macOS (Intel or Apple Silicon)
- Python 3.11+
- [Claude Desktop](https://claude.ai/download)
- Freshdesk API key — **Profile Settings → Your API Key** in Freshdesk

---

## Quick Start

### 1. Install dependencies

```bash
cd ~/freshdesk-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

#### Step 2.1: Find the correct configuration location

The Claude Desktop config file location depends on your OS:

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

#### Step 2.2: Create or edit the config file

**If the file doesn't exist**, create it with this content:

```json
{
  "mcpServers": {
    "freshdesk": {
      "command": "/Users/YOUR_USERNAME/freshdesk-mcp/.venv/bin/python",
      "args": ["/Users/YOUR_USERNAME/freshdesk-mcp/server.py"],
      "env": {
        "FRESHDESK_DOMAIN": "your-domain.freshdesk.com",
        "FRESHDESK_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**If the file already exists**, add only the `freshdesk` section under `mcpServers` (keep existing servers):

```json
{
  "mcpServers": {
    "existing-server": { ... },
    "freshdesk": {
      "command": "/Users/YOUR_USERNAME/freshdesk-mcp/.venv/bin/python",
      "args": ["/Users/YOUR_USERNAME/freshdesk-mcp/server.py"],
      "env": {
        "FRESHDESK_DOMAIN": "your-domain.freshdesk.com",
        "FRESHDESK_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### Step 2.3: Replace the placeholder values

| Placeholder | What to replace with | How to find |
|-------------|---------------------|-------------|
| `YOUR_USERNAME` | Your system username | Run `whoami` in Terminal |
| `your-domain.freshdesk.com` | Your Freshdesk domain | From your Freshdesk URL (e.g., `company.freshdesk.com`) |
| `your_api_key_here` | Your Freshdesk API key | **Profile Settings → API Key** in Freshdesk |

**Example with real values (macOS):**
```json
{
  "mcpServers": {
    "freshdesk": {
      "command": "/Users/john/freshdesk-mcp/.venv/bin/python",
      "args": ["/Users/john/freshdesk-mcp/server.py"],
      "env": {
        "FRESHDESK_DOMAIN": "acme-corp.freshdesk.com",
        "FRESHDESK_API_KEY": "abcdef123456789"
      }
    }
  }
}
```

#### Step 2.4: Validate your JSON

Make sure your JSON is valid:
- All quotes are straight quotes `"`, not curly quotes
- No trailing commas after the last property
- Brackets and braces are properly closed

**Tip:** Use an online JSON validator if unsure.

### 3. Restart Claude Desktop

Quit and reopen. The `fd_*` tools will appear automatically.

---

## Tool Reference

All tools are prefixed `fd_`. Every response includes a `rate_limit` block:

```json
"rate_limit": { "total": "700", "remaining": "695", "used": "1" }
```

---

### Tickets

#### `fd_search_tickets`
Search using [Freshdesk query syntax](https://developers.freshdesk.com/api/#filter_tickets).

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `query` | string | ✅ | e.g. `status:2`, `priority:3`, `tag:billing`, free text |
| `page` | integer | | Default: 1 |
| `per_page` | integer | | Max 30, default 15 |

**Query examples:** `status:2` (open), `priority:3` (high), `agent_id:42`, `"login issue"` (free text)

---

#### `fd_list_tickets`
Browse tickets with filters.

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `filter` | string | `new_and_my_open` | `new_and_my_open` \| `watching` \| `spam` \| `deleted` |
| `order_by` | string | `created_at` | `created_at` \| `due_by` \| `updated_at` \| `status` |
| `order_type` | string | `desc` | `asc` \| `desc` |
| `page` | integer | 1 | |
| `per_page` | integer | 30 | Max 100 |
| `include` | string | | Comma-separated: `requester`, `company`, `stats`, `description` |

---

#### `fd_get_ticket`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `ticket_id` | integer | ✅ | |
| `include_conversations` | boolean | | Default: true |

---

#### `fd_create_ticket`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `subject` | string | ✅ | |
| `description` | string | ✅ | HTML or plain text |
| `email` | string | ✅ | Requester email |
| `name` | string | | Requester display name |
| `phone` | string | | |
| `priority` | integer | | 1=Low 2=Medium 3=High 4=Urgent (default: 2) |
| `status` | integer | | 2=Open 3=Pending 4=Resolved 5=Closed (default: 2) |
| `source` | integer | | 1=Email 2=Portal 3=Phone 7=Chat 9=Feedback |
| `type` | string | | Account-specific ticket type |
| `tags` | array | | |
| `group_id` | integer | | |
| `responder_id` | integer | | |
| `due_by` | string | | ISO 8601, e.g. `2025-06-01T17:00:00Z` |
| `cc_emails` | array | | |

---

#### `fd_update_ticket`
Only `ticket_id` is required; all other fields are optional.

| Parameter | Type | Notes |
|-----------|------|-------|
| `ticket_id` | integer | ✅ Required |
| `status` | integer | 2=Open 3=Pending 4=Resolved 5=Closed |
| `priority` | integer | 1=Low 2=Medium 3=High 4=Urgent |
| `responder_id` | integer | |
| `group_id` | integer | |
| `type` | string | |
| `tags` | array | Replaces existing tags |
| `subject` | string | |
| `due_by` | string | ISO 8601 |
| `source` | integer | |

---

#### `fd_delete_ticket`
Soft delete — moves to Trash. Recoverable within 30 days.

| Parameter | Type | Required |
|-----------|------|----------|
| `ticket_id` | integer | ✅ |

---

#### `fd_restore_ticket`

| Parameter | Type | Required |
|-----------|------|----------|
| `ticket_id` | integer | ✅ |

---

#### `fd_list_ticket_fields`
No parameters. Returns all field definitions including custom fields — useful for finding `custom_field` key names.

---

### Conversations

#### `fd_reply_ticket`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `ticket_id` | integer | ✅ | |
| `body` | string | ✅ | HTML or plain text |
| `private` | boolean | | `true` = internal note, `false` = public reply (default) |
| `cc_emails` | array | | Public replies only |
| `bcc_emails` | array | | Public replies only |

---

#### `fd_update_conversation`

| Parameter | Type | Required |
|-----------|------|----------|
| `conversation_id` | integer | ✅ |
| `body` | string | ✅ |

---

#### `fd_delete_conversation`

| Parameter | Type | Required |
|-----------|------|----------|
| `conversation_id` | integer | ✅ |

---

### Contacts

#### `fd_search_contacts`
Use `term` for name-prefix autocomplete, or field filters for exact match.

| Parameter | Type | Notes |
|-----------|------|-------|
| `term` | string | Name prefix |
| `email` | string | Exact match |
| `mobile` | string | |
| `phone` | string | |
| `company_id` | integer | |
| `page` | integer | |

---

#### `fd_get_contact`

| Parameter | Type | Required |
|-----------|------|----------|
| `contact_id` | integer | ✅ |

---

#### `fd_create_contact`

| Parameter | Type | Required |
|-----------|------|----------|
| `name` | string | ✅ |
| `email` | string | |
| `phone` | string | |
| `mobile` | string | |
| `company_id` | integer | |
| `job_title` | string | |
| `tags` | array | |
| `description` | string | |

---

#### `fd_update_contact`
Same fields as create, plus `contact_id` (✅ required).

---

#### `fd_delete_contact`

| Parameter | Type | Notes |
|-----------|------|-------|
| `contact_id` | integer | ✅ Required |
| `permanently` | boolean | Hard delete — irreversible (default: false) |

---

#### `fd_merge_contacts`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `primary_id` | integer | ✅ | Contact to keep |
| `secondary_ids` | array | ✅ | Contact IDs to absorb |

---

### Companies

#### `fd_search_companies`

| Parameter | Type | Required |
|-----------|------|----------|
| `term` | string | ✅ Name prefix |
| `page` | integer | |

---

#### `fd_get_company` / `fd_delete_company`

| Parameter | Type | Required |
|-----------|------|----------|
| `company_id` | integer | ✅ |

> Note: deleting a company does not delete its contacts.

---

#### `fd_create_company`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `name` | string | ✅ | |
| `description` | string | | |
| `domains` | array | | Email domains, e.g. `["acme.com"]` |
| `note` | string | | |
| `health_score` | string | | |
| `account_tier` | string | | |
| `renewal_date` | string | | ISO date |
| `industry` | string | | |

---

#### `fd_update_company`
Same fields as create, plus `company_id` (✅ required).

---

### Agents

#### `fd_list_agents`

| Parameter | Type | Notes |
|-----------|------|-------|
| `email` | string | Filter by email |
| `mobile` | string | |
| `state` | string | `fulltime` or `occasional` |
| `page` | integer | |

---

#### `fd_get_agent`

| Parameter | Type | Required |
|-----------|------|----------|
| `agent_id` | integer | ✅ |

---

#### `fd_current_agent`
No parameters. Returns the profile of the agent whose API key is configured.

---

#### `fd_update_agent`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `agent_id` | integer | ✅ | |
| `available` | boolean | | Online/offline for auto-assignment |
| `ticket_scope` | integer | | 1=Global 2=Group 3=Assigned |
| `group_ids` | array | | Group membership |

---

### Groups

#### `fd_list_groups`
No parameters.

#### `fd_get_group`

| Parameter | Type | Required |
|-----------|------|----------|
| `group_id` | integer | ✅ |

---

### Canned Responses

#### `fd_list_canned_response_folders`
No parameters. Returns folder IDs — use with `fd_list_canned_responses`.

#### `fd_list_canned_responses`

| Parameter | Type | Required |
|-----------|------|----------|
| `folder_id` | integer | ✅ |

#### `fd_get_canned_response`

| Parameter | Type | Required |
|-----------|------|----------|
| `canned_response_id` | integer | ✅ |

#### `fd_search_canned_responses`

| Parameter | Type | Required |
|-----------|------|----------|
| `term` | string | ✅ |

---

### Solution Articles (Knowledge Base)

#### `fd_search_solution_articles`

| Parameter | Type | Required |
|-----------|------|----------|
| `term` | string | ✅ |

#### `fd_list_solution_categories`
No parameters.

#### `fd_list_solution_folders`

| Parameter | Type | Required |
|-----------|------|----------|
| `category_id` | integer | ✅ |

#### `fd_list_solution_articles`

| Parameter | Type | Required |
|-----------|------|----------|
| `folder_id` | integer | ✅ |
| `page` | integer | |

#### `fd_get_solution_article`

| Parameter | Type | Required |
|-----------|------|----------|
| `article_id` | integer | ✅ |

---

### Time Entries

#### `fd_list_time_entries`

| Parameter | Type | Required |
|-----------|------|----------|
| `ticket_id` | integer | ✅ |

---

### Satisfaction Ratings

#### `fd_get_satisfaction_rating`

| Parameter | Type | Required |
|-----------|------|----------|
| `ticket_id` | integer | ✅ |

---

## Example prompts

```
Show me all open high-priority tickets.

Search for tickets tagged "billing" sorted by most recently updated.

Create a ticket for jan.kowalski@example.com —
  subject: "Cannot access account", priority: High, group: Support.

Add a private internal note to ticket #1234:
  "Waiting for confirmation from the infrastructure team."

Reply to ticket #5678:
  "Thank you for reporting this. We've identified the issue and are working on a fix."

Find the contact for email jan.kowalski@example.com and update their job title to "CTO".

Merge contact ID 99 into contact ID 42.

Search the knowledge base for articles about "password reset".

List all canned responses in the "Billing" folder.

Show me all agents in the "Tier 2 Support" group and their availability.

List all time entries logged against ticket #3344.
```

---

## Troubleshooting

### Tools don't appear in Claude Desktop

```bash
# Verify the server starts without errors
cd ~/freshdesk-mcp
source .venv/bin/activate
FRESHDESK_DOMAIN=shortlistassist.freshdesk.com \
FRESHDESK_API_KEY=your_api_key_here \
python server.py
# Should block silently — no errors = OK. Ctrl+C to exit.
```

Check MCP logs:

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

### `401 Unauthorized`
API key is wrong or revoked. Regenerate under **Profile Settings → API Key** in Freshdesk.

### `403 Forbidden`
The API key owner's role doesn't permit that action. Freshdesk enforces role-based access at the API level.

### `429 Too Many Requests`
Rate limit reached. Freshdesk allows ~700 calls/hour on most plans. The `rate_limit.remaining` field in each response shows your current quota.

---

## Security

- The API key lives only in `claude_desktop_config.json` on the local machine.
- All traffic goes directly from `server.py` to your Freshdesk domain over HTTPS. Nothing passes through Anthropic infrastructure.
- To rotate the key: update `env.FRESHDESK_API_KEY` in the config and restart Claude Desktop.
