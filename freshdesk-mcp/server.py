#!/usr/bin/env python3
"""
Freshdesk MCP Server — Full Coverage
Exposes all major Freshdesk API v2 resources as MCP tools for Claude Desktop.

Modules covered:
  - Tickets (CRUD, search, list, restore, bulk)
  - Conversations (replies, notes, update, delete)
  - Contacts (CRUD, search, merge)
  - Companies (CRUD, search)
  - Agents (list, get, update, current)
  - Groups (list, get)
  - Canned Responses (folders, list, get, search)
  - Solution Articles (search, categories, folders, articles)
  - Time Entries (list by ticket)
  - Satisfaction Ratings (get by ticket)
"""

import os
import json
import httpx
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

FD_DOMAIN  = os.environ["FRESHDESK_DOMAIN"]   # e.g. shortlistassist.freshdesk.com
FD_API_KEY = os.environ["FRESHDESK_API_KEY"]
BASE_URL   = f"https://{FD_DOMAIN}/api/v2"

server = Server("freshdesk-mcp")


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        auth=(FD_API_KEY, "X"),
        headers={"Content-Type": "application/json"},
        timeout=30,
    )


def _ok(data: Any, *, rate: dict | None = None) -> list[TextContent]:
    payload: dict[str, Any] = {"data": data}
    if rate:
        payload["rate_limit"] = rate
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


def _err(msg: str, status: int | None = None, body: str | None = None) -> list[TextContent]:
    payload: dict[str, Any] = {"error": msg}
    if status:
        payload["http_status"] = status
    if body:
        try:
            payload["detail"] = json.loads(body)
        except Exception:
            payload["detail"] = body[:400]
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


def _rate(r: httpx.Response) -> dict:
    return {
        "total":     r.headers.get("X-Ratelimit-Total"),
        "remaining": r.headers.get("X-Ratelimit-Remaining"),
        "used":      r.headers.get("X-Ratelimit-Used-CurrentRequest"),
    }


def _check(r: httpx.Response, ok_codes: tuple = (200, 201)) -> str | None:
    if r.status_code not in ok_codes:
        return f"HTTP {r.status_code}"
    return None


# ── Tool definitions ───────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [

        # ── TICKETS ──────────────────────────────────────────────────────────

        Tool(
            name="fd_search_tickets",
            description=(
                "Search tickets using Freshdesk query syntax. "
                "Examples: 'status:2' (open), 'priority:3' (high), "
                "'agent_id:42', 'tag:billing', or free-text keyword. "
                "Returns paginated results (max 30 per page, max 300 total via paging)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query":    {"type": "string"},
                    "page":     {"type": "integer", "default": 1},
                    "per_page": {"type": "integer", "description": "Max 30.", "default": 15},
                },
                "required": ["query"],
            },
        ),

        Tool(
            name="fd_list_tickets",
            description=(
                "List tickets with optional filters. "
                "filter: 'new_and_my_open' | 'watching' | 'spam' | 'deleted'. "
                "order_by: 'created_at' | 'due_by' | 'updated_at' | 'status'. "
                "include: comma-separated 'requester,company,stats,description'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter":     {"type": "string", "default": "new_and_my_open"},
                    "order_by":   {"type": "string", "default": "created_at"},
                    "order_type": {"type": "string", "default": "desc"},
                    "page":       {"type": "integer", "default": 1},
                    "per_page":   {"type": "integer", "description": "Max 100.", "default": 30},
                    "include":    {"type": "string"},
                },
            },
        ),

        Tool(
            name="fd_get_ticket",
            description="Fetch full details of a single ticket, optionally including conversation thread.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id":             {"type": "integer"},
                    "include_conversations": {"type": "boolean", "default": True},
                },
                "required": ["ticket_id"],
            },
        ),

        Tool(
            name="fd_create_ticket",
            description="Create a new ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject":      {"type": "string"},
                    "description":  {"type": "string", "description": "HTML or plain-text body."},
                    "email":        {"type": "string"},
                    "name":         {"type": "string"},
                    "phone":        {"type": "string"},
                    "priority":     {"type": "integer", "description": "1=Low 2=Medium 3=High 4=Urgent.", "default": 2},
                    "status":       {"type": "integer", "description": "2=Open 3=Pending 4=Resolved 5=Closed.", "default": 2},
                    "source":       {"type": "integer", "description": "1=Email 2=Portal 3=Phone 7=Chat 9=Feedback."},
                    "type":         {"type": "string"},
                    "tags":         {"type": "array", "items": {"type": "string"}},
                    "group_id":     {"type": "integer"},
                    "responder_id": {"type": "integer"},
                    "due_by":       {"type": "string", "description": "ISO 8601, e.g. '2025-06-01T17:00:00Z'."},
                    "cc_emails":    {"type": "array", "items": {"type": "string"}},
                },
                "required": ["subject", "description", "email"],
            },
        ),

        Tool(
            name="fd_update_ticket",
            description="Update ticket fields: status, priority, assignee, group, tags, subject, due_by, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id":    {"type": "integer"},
                    "status":       {"type": "integer"},
                    "priority":     {"type": "integer"},
                    "responder_id": {"type": "integer"},
                    "group_id":     {"type": "integer"},
                    "type":         {"type": "string"},
                    "tags":         {"type": "array", "items": {"type": "string"}},
                    "subject":      {"type": "string"},
                    "due_by":       {"type": "string"},
                    "source":       {"type": "integer"},
                },
                "required": ["ticket_id"],
            },
        ),

        Tool(
            name="fd_delete_ticket",
            description="Move ticket to Trash (soft delete). Recoverable within 30 days.",
            inputSchema={
                "type": "object",
                "properties": {"ticket_id": {"type": "integer"}},
                "required": ["ticket_id"],
            },
        ),

        Tool(
            name="fd_restore_ticket",
            description="Restore a ticket from Trash.",
            inputSchema={
                "type": "object",
                "properties": {"ticket_id": {"type": "integer"}},
                "required": ["ticket_id"],
            },
        ),

        Tool(
            name="fd_list_ticket_fields",
            description="List all ticket field definitions including custom fields.",
            inputSchema={"type": "object", "properties": {}},
        ),

        # ── CONVERSATIONS ────────────────────────────────────────────────────

        Tool(
            name="fd_reply_ticket",
            description=(
                "Add a public reply (emailed to requester) or a private agent note. "
                "private=true → internal note only. Supports CC/BCC for public replies."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id":  {"type": "integer"},
                    "body":       {"type": "string", "description": "HTML or plain text."},
                    "private":    {"type": "boolean", "default": False},
                    "cc_emails":  {"type": "array", "items": {"type": "string"}},
                    "bcc_emails": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["ticket_id", "body"],
            },
        ),

        Tool(
            name="fd_update_conversation",
            description="Edit the body of an existing reply or note.",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "integer"},
                    "body":            {"type": "string"},
                },
                "required": ["conversation_id", "body"],
            },
        ),

        Tool(
            name="fd_delete_conversation",
            description="Delete a conversation entry (reply or note) from a ticket.",
            inputSchema={
                "type": "object",
                "properties": {"conversation_id": {"type": "integer"}},
                "required": ["conversation_id"],
            },
        ),

        # ── CONTACTS ────────────────────────────────────────────────────────

        Tool(
            name="fd_search_contacts",
            description=(
                "Search contacts. Use 'term' for name-prefix autocomplete. "
                "Or filter by email / mobile / phone / company_id."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "term":       {"type": "string"},
                    "email":      {"type": "string"},
                    "mobile":     {"type": "string"},
                    "phone":      {"type": "string"},
                    "company_id": {"type": "integer"},
                    "page":       {"type": "integer", "default": 1},
                },
            },
        ),

        Tool(
            name="fd_get_contact",
            description="Get full details of a contact by ID.",
            inputSchema={
                "type": "object",
                "properties": {"contact_id": {"type": "integer"}},
                "required": ["contact_id"],
            },
        ),

        Tool(
            name="fd_create_contact",
            description="Create a new contact (customer/requester).",
            inputSchema={
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "email":       {"type": "string"},
                    "phone":       {"type": "string"},
                    "mobile":      {"type": "string"},
                    "company_id":  {"type": "integer"},
                    "job_title":   {"type": "string"},
                    "tags":        {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                },
                "required": ["name"],
            },
        ),

        Tool(
            name="fd_update_contact",
            description="Update an existing contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id":  {"type": "integer"},
                    "name":        {"type": "string"},
                    "email":       {"type": "string"},
                    "phone":       {"type": "string"},
                    "mobile":      {"type": "string"},
                    "company_id":  {"type": "integer"},
                    "job_title":   {"type": "string"},
                    "tags":        {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                },
                "required": ["contact_id"],
            },
        ),

        Tool(
            name="fd_delete_contact",
            description="Soft-delete a contact. Set permanently=true for hard delete (irreversible).",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id":  {"type": "integer"},
                    "permanently": {"type": "boolean", "default": False},
                },
                "required": ["contact_id"],
            },
        ),

        Tool(
            name="fd_merge_contacts",
            description="Merge duplicate contacts into a primary contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "primary_id":    {"type": "integer", "description": "Contact ID to keep."},
                    "secondary_ids": {"type": "array", "items": {"type": "integer"}, "description": "IDs to absorb."},
                },
                "required": ["primary_id", "secondary_ids"],
            },
        ),

        # ── COMPANIES ───────────────────────────────────────────────────────

        Tool(
            name="fd_search_companies",
            description="Search companies by name prefix.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "page": {"type": "integer", "default": 1},
                },
                "required": ["term"],
            },
        ),

        Tool(
            name="fd_get_company",
            description="Get full details of a company by ID.",
            inputSchema={
                "type": "object",
                "properties": {"company_id": {"type": "integer"}},
                "required": ["company_id"],
            },
        ),

        Tool(
            name="fd_create_company",
            description="Create a new company record.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name":         {"type": "string"},
                    "description":  {"type": "string"},
                    "domains":      {"type": "array", "items": {"type": "string"}, "description": "e.g. ['acme.com']"},
                    "note":         {"type": "string"},
                    "health_score": {"type": "string"},
                    "account_tier": {"type": "string"},
                    "renewal_date": {"type": "string", "description": "ISO date."},
                    "industry":     {"type": "string"},
                },
                "required": ["name"],
            },
        ),

        Tool(
            name="fd_update_company",
            description="Update an existing company.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id":   {"type": "integer"},
                    "name":         {"type": "string"},
                    "description":  {"type": "string"},
                    "domains":      {"type": "array", "items": {"type": "string"}},
                    "note":         {"type": "string"},
                    "health_score": {"type": "string"},
                    "account_tier": {"type": "string"},
                    "renewal_date": {"type": "string"},
                    "industry":     {"type": "string"},
                },
                "required": ["company_id"],
            },
        ),

        Tool(
            name="fd_delete_company",
            description="Delete a company record. Does NOT delete its contacts.",
            inputSchema={
                "type": "object",
                "properties": {"company_id": {"type": "integer"}},
                "required": ["company_id"],
            },
        ),

        # ── AGENTS ──────────────────────────────────────────────────────────

        Tool(
            name="fd_list_agents",
            description="List agents. Filter by email, mobile, phone, or state (fulltime/occasional).",
            inputSchema={
                "type": "object",
                "properties": {
                    "email":  {"type": "string"},
                    "mobile": {"type": "string"},
                    "state":  {"type": "string", "description": "'fulltime' or 'occasional'."},
                    "page":   {"type": "integer", "default": 1},
                },
            },
        ),

        Tool(
            name="fd_get_agent",
            description="Get details of a specific agent by ID.",
            inputSchema={
                "type": "object",
                "properties": {"agent_id": {"type": "integer"}},
                "required": ["agent_id"],
            },
        ),

        Tool(
            name="fd_current_agent",
            description="Get the profile of the agent authenticated by the configured API key.",
            inputSchema={"type": "object", "properties": {}},
        ),

        Tool(
            name="fd_update_agent",
            description="Update an agent's availability, ticket scope, or group membership.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id":     {"type": "integer"},
                    "available":    {"type": "boolean"},
                    "ticket_scope": {"type": "integer", "description": "1=Global 2=Group 3=Assigned."},
                    "group_ids":    {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["agent_id"],
            },
        ),

        # ── GROUPS ──────────────────────────────────────────────────────────

        Tool(
            name="fd_list_groups",
            description="List all agent groups.",
            inputSchema={"type": "object", "properties": {}},
        ),

        Tool(
            name="fd_get_group",
            description="Get details and agent membership of a specific group.",
            inputSchema={
                "type": "object",
                "properties": {"group_id": {"type": "integer"}},
                "required": ["group_id"],
            },
        ),

        # ── CANNED RESPONSES ────────────────────────────────────────────────

        Tool(
            name="fd_list_canned_response_folders",
            description="List all canned response folders.",
            inputSchema={"type": "object", "properties": {}},
        ),

        Tool(
            name="fd_list_canned_responses",
            description="List all canned responses inside a specific folder.",
            inputSchema={
                "type": "object",
                "properties": {"folder_id": {"type": "integer"}},
                "required": ["folder_id"],
            },
        ),

        Tool(
            name="fd_get_canned_response",
            description="Get the full content (HTML body) of a specific canned response.",
            inputSchema={
                "type": "object",
                "properties": {"canned_response_id": {"type": "integer"}},
                "required": ["canned_response_id"],
            },
        ),

        # ── SOLUTION ARTICLES ────────────────────────────────────────────────

        Tool(
            name="fd_search_solution_articles",
            description="Search knowledge base solution articles by keyword.",
            inputSchema={
                "type": "object",
                "properties": {"term": {"type": "string"}},
                "required": ["term"],
            },
        ),

        Tool(
            name="fd_list_solution_categories",
            description="List all top-level knowledge base categories.",
            inputSchema={"type": "object", "properties": {}},
        ),

        Tool(
            name="fd_list_solution_folders",
            description="List solution folders within a category.",
            inputSchema={
                "type": "object",
                "properties": {"category_id": {"type": "integer"}},
                "required": ["category_id"],
            },
        ),

        Tool(
            name="fd_list_solution_articles",
            description="List solution articles within a folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "integer"},
                    "page":      {"type": "integer", "default": 1},
                },
                "required": ["folder_id"],
            },
        ),

        Tool(
            name="fd_get_solution_article",
            description="Get the full content of a solution article by ID.",
            inputSchema={
                "type": "object",
                "properties": {"article_id": {"type": "integer"}},
                "required": ["article_id"],
            },
        ),

        # ── TIME ENTRIES ─────────────────────────────────────────────────────

        Tool(
            name="fd_list_time_entries",
            description="List time entries logged against a ticket.",
            inputSchema={
                "type": "object",
                "properties": {"ticket_id": {"type": "integer"}},
                "required": ["ticket_id"],
            },
        ),

        # ── SATISFACTION RATINGS ─────────────────────────────────────────────

        Tool(
            name="fd_get_satisfaction_rating",
            description="Get the CSAT satisfaction rating submitted for a ticket.",
            inputSchema={
                "type": "object",
                "properties": {"ticket_id": {"type": "integer"}},
                "required": ["ticket_id"],
            },
        ),

    ]  # end list_tools


# ── Tool call dispatcher ───────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    async with _client() as c:

        # ── TICKETS ───────────────────────────────────────────────────────────

        if name == "fd_search_tickets":
            q        = arguments["query"]
            page     = arguments.get("page", 1)
            per_page = min(arguments.get("per_page", 15), 30)
            r = await c.get(f"{BASE_URL}/search/tickets",
                            params={"query": f'"{q}"', "page": page})
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            d = r.json()
            tickets = [
                {k: t.get(k) for k in (
                    "id","subject","status","priority","type","tags",
                    "requester_id","responder_id","group_id",
                    "created_at","updated_at","due_by"
                )}
                for t in d.get("results", [])[:per_page]
            ]
            return _ok({"total": d.get("total", 0), "page": page, "tickets": tickets},
                       rate=_rate(r))

        elif name == "fd_list_tickets":
            params: dict[str, Any] = {
                "filter":     arguments.get("filter", "new_and_my_open"),
                "order_by":   arguments.get("order_by", "created_at"),
                "order_type": arguments.get("order_type", "desc"),
                "page":       arguments.get("page", 1),
                "per_page":   min(arguments.get("per_page", 30), 100),
            }
            if inc := arguments.get("include"):
                params["include"] = inc
            r = await c.get(f"{BASE_URL}/tickets", params=params)
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_get_ticket":
            tid = arguments["ticket_id"]
            r = await c.get(f"{BASE_URL}/tickets/{tid}")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            ticket = r.json()
            convs: list = []
            if arguments.get("include_conversations", True):
                rc = await c.get(f"{BASE_URL}/tickets/{tid}/conversations")
                if rc.status_code == 200:
                    convs = rc.json()
            return _ok({"ticket": ticket, "conversations": convs}, rate=_rate(r))

        elif name == "fd_create_ticket":
            payload: dict[str, Any] = {}
            for k in ("subject","description","email","priority","status",
                      "name","phone","source","type","tags",
                      "group_id","responder_id","due_by","cc_emails"):
                if k in arguments:
                    payload[k] = arguments[k]
            r = await c.post(f"{BASE_URL}/tickets", json=payload)
            if e := _check(r, (200, 201)):
                return _err(e, r.status_code, r.text)
            t = r.json()
            return _ok({"created": True, "ticket_id": t["id"], "subject": t["subject"]},
                       rate=_rate(r))

        elif name == "fd_update_ticket":
            tid = arguments["ticket_id"]
            fields = {k: arguments[k] for k in (
                "status","priority","responder_id","group_id",
                "type","tags","subject","due_by","source"
            ) if k in arguments}
            if not fields:
                return _err("No fields to update.")
            r = await c.put(f"{BASE_URL}/tickets/{tid}", json=fields)
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok({"updated": True, "ticket_id": tid, "changes": fields},
                       rate=_rate(r))

        elif name == "fd_delete_ticket":
            tid = arguments["ticket_id"]
            r = await c.delete(f"{BASE_URL}/tickets/{tid}")
            if e := _check(r, (200, 204)):
                return _err(e, r.status_code, r.text)
            return _ok({"deleted": True, "ticket_id": tid}, rate=_rate(r))

        elif name == "fd_restore_ticket":
            tid = arguments["ticket_id"]
            r = await c.put(f"{BASE_URL}/tickets/{tid}/restore")
            if e := _check(r, (200, 204)):
                return _err(e, r.status_code, r.text)
            return _ok({"restored": True, "ticket_id": tid}, rate=_rate(r))

        elif name == "fd_list_ticket_fields":
            r = await c.get(f"{BASE_URL}/ticket_fields")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        # ── CONVERSATIONS ─────────────────────────────────────────────────────

        elif name == "fd_reply_ticket":
            tid     = arguments["ticket_id"]
            body    = arguments["body"]
            private = arguments.get("private", False)
            pl: dict[str, Any] = {"body": body}
            if private:
                pl["private"] = True
                endpoint = f"{BASE_URL}/tickets/{tid}/notes"
            else:
                endpoint = f"{BASE_URL}/tickets/{tid}/reply"
                for k in ("cc_emails", "bcc_emails"):
                    if k in arguments:
                        pl[k] = arguments[k]
            r = await c.post(endpoint, json=pl)
            if e := _check(r, (200, 201)):
                return _err(e, r.status_code, r.text)
            return _ok({
                "posted": True,
                "private": private,
                "conversation_id": r.json().get("id"),
            }, rate=_rate(r))

        elif name == "fd_update_conversation":
            cid = arguments["conversation_id"]
            r = await c.put(f"{BASE_URL}/conversations/{cid}",
                            json={"body": arguments["body"]})
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok({"updated": True, "conversation_id": cid}, rate=_rate(r))

        elif name == "fd_delete_conversation":
            cid = arguments["conversation_id"]
            r = await c.delete(f"{BASE_URL}/conversations/{cid}")
            if e := _check(r, (200, 204)):
                return _err(e, r.status_code, r.text)
            return _ok({"deleted": True, "conversation_id": cid}, rate=_rate(r))

        # ── CONTACTS ──────────────────────────────────────────────────────────

        elif name == "fd_search_contacts":
            if term := arguments.get("term"):
                r = await c.get(f"{BASE_URL}/contacts/autocomplete", params={"term": term})
            else:
                params = {k: arguments[k] for k in
                          ("email","mobile","phone","company_id","page")
                          if k in arguments}
                r = await c.get(f"{BASE_URL}/contacts", params=params)
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_get_contact":
            r = await c.get(f"{BASE_URL}/contacts/{arguments['contact_id']}")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_create_contact":
            pl = {k: arguments[k] for k in (
                "name","email","phone","mobile","company_id",
                "job_title","tags","description"
            ) if k in arguments}
            r = await c.post(f"{BASE_URL}/contacts", json=pl)
            if e := _check(r, (200, 201)):
                return _err(e, r.status_code, r.text)
            ct = r.json()
            return _ok({"created": True, "contact_id": ct["id"], "name": ct.get("name")},
                       rate=_rate(r))

        elif name == "fd_update_contact":
            cid = arguments["contact_id"]
            fields = {k: arguments[k] for k in (
                "name","email","phone","mobile","company_id",
                "job_title","tags","description"
            ) if k in arguments}
            r = await c.put(f"{BASE_URL}/contacts/{cid}", json=fields)
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok({"updated": True, "contact_id": cid}, rate=_rate(r))

        elif name == "fd_delete_contact":
            cid  = arguments["contact_id"]
            perm = arguments.get("permanently", False)
            if perm:
                r = await c.delete(f"{BASE_URL}/contacts/{cid}/hard_delete",
                                   params={"force": True})
            else:
                r = await c.delete(f"{BASE_URL}/contacts/{cid}")
            if e := _check(r, (200, 204)):
                return _err(e, r.status_code, r.text)
            return _ok({"deleted": True, "contact_id": cid, "permanent": perm},
                       rate=_rate(r))

        elif name == "fd_merge_contacts":
            r = await c.post(f"{BASE_URL}/contacts/merge", json={
                "primary_contact_id":    arguments["primary_id"],
                "secondary_contact_ids": arguments["secondary_ids"],
            })
            if e := _check(r, (200, 201)):
                return _err(e, r.status_code, r.text)
            return _ok({"merged": True, "primary_id": arguments["primary_id"],
                        "absorbed": arguments["secondary_ids"]}, rate=_rate(r))

        # ── COMPANIES ─────────────────────────────────────────────────────────

        elif name == "fd_search_companies":
            r = await c.get(f"{BASE_URL}/companies/autocomplete",
                            params={"name": arguments["term"]})
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_get_company":
            r = await c.get(f"{BASE_URL}/companies/{arguments['company_id']}")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_create_company":
            pl = {k: arguments[k] for k in (
                "name","description","domains","note",
                "health_score","account_tier","renewal_date","industry"
            ) if k in arguments}
            r = await c.post(f"{BASE_URL}/companies", json=pl)
            if e := _check(r, (200, 201)):
                return _err(e, r.status_code, r.text)
            co = r.json()
            return _ok({"created": True, "company_id": co["id"], "name": co.get("name")},
                       rate=_rate(r))

        elif name == "fd_update_company":
            cid = arguments["company_id"]
            fields = {k: arguments[k] for k in (
                "name","description","domains","note",
                "health_score","account_tier","renewal_date","industry"
            ) if k in arguments}
            r = await c.put(f"{BASE_URL}/companies/{cid}", json=fields)
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok({"updated": True, "company_id": cid}, rate=_rate(r))

        elif name == "fd_delete_company":
            cid = arguments["company_id"]
            r = await c.delete(f"{BASE_URL}/companies/{cid}")
            if e := _check(r, (200, 204)):
                return _err(e, r.status_code, r.text)
            return _ok({"deleted": True, "company_id": cid}, rate=_rate(r))

        # ── AGENTS ────────────────────────────────────────────────────────────

        elif name == "fd_list_agents":
            params = {k: arguments[k] for k in
                      ("email","mobile","state","page") if k in arguments}
            r = await c.get(f"{BASE_URL}/agents", params=params)
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_get_agent":
            r = await c.get(f"{BASE_URL}/agents/{arguments['agent_id']}")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_current_agent":
            r = await c.get(f"{BASE_URL}/agents/me")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_update_agent":
            aid = arguments["agent_id"]
            fields = {k: arguments[k] for k in (
                "available","ticket_scope","group_ids"
            ) if k in arguments}
            r = await c.put(f"{BASE_URL}/agents/{aid}", json=fields)
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok({"updated": True, "agent_id": aid}, rate=_rate(r))

        # ── GROUPS ────────────────────────────────────────────────────────────

        elif name == "fd_list_groups":
            r = await c.get(f"{BASE_URL}/groups")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_get_group":
            r = await c.get(f"{BASE_URL}/groups/{arguments['group_id']}")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        # ── CANNED RESPONSES ──────────────────────────────────────────────────

        elif name == "fd_list_canned_response_folders":
            r = await c.get(f"{BASE_URL}/canned_response_folders")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_list_canned_responses":
            fid = arguments["folder_id"]
            r = await c.get(f"{BASE_URL}/canned_response_folders/{fid}/responses")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_get_canned_response":
            r = await c.get(f"{BASE_URL}/canned_responses/{arguments['canned_response_id']}")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        # ── SOLUTION ARTICLES ─────────────────────────────────────────────────

        elif name == "fd_search_solution_articles":
            r = await c.get(f"{BASE_URL}/search/solutions",
                            params={"term": arguments["term"]})
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_list_solution_categories":
            r = await c.get(f"{BASE_URL}/solutions/categories")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_list_solution_folders":
            cat_id = arguments["category_id"]
            r = await c.get(f"{BASE_URL}/solutions/categories/{cat_id}/folders")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_list_solution_articles":
            fid = arguments["folder_id"]
            r = await c.get(f"{BASE_URL}/solutions/folders/{fid}/articles",
                            params={"page": arguments.get("page", 1)})
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        elif name == "fd_get_solution_article":
            r = await c.get(f"{BASE_URL}/solutions/articles/{arguments['article_id']}")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        # ── TIME ENTRIES ──────────────────────────────────────────────────────

        elif name == "fd_list_time_entries":
            r = await c.get(f"{BASE_URL}/tickets/{arguments['ticket_id']}/time_entries")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        # ── SATISFACTION RATINGS ──────────────────────────────────────────────

        elif name == "fd_get_satisfaction_rating":
            r = await c.get(f"{BASE_URL}/tickets/{arguments['ticket_id']}/satisfaction_ratings")
            if e := _check(r):
                return _err(e, r.status_code, r.text)
            return _ok(r.json(), rate=_rate(r))

        else:
            return _err(f"Unknown tool: {name}")


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream,
                         server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
