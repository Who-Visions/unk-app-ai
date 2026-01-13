"""
Notion Integration Skill
========================
Handles interactions with Notion API for project management and observablity.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from notion_client import Client
from notion_client.errors import APIResponseError

# Notion Database IDs
# -------------------
# Core Projects
DB_WEB_PROJECTS = "17b82401539180769b55c27591605380"
DB_PHOTO_PROJECTS = "17b82401539180f19c96f2a35368686d"
DB_PROJECT_TRACKER = "17b824015391800c8f12c9869150047d"

# Verified Database IDs (from Hierarchy Crawl)
DB_CONTRACTS = "2a5555950e2045d4942f8568b68b316f"
DB_METRICS_LOG = "d17006d5c557416688cfd3a7df1f8d8c"
DB_CONTENT_LIBRARY = "d23d02a7bec54167b6179111c5a48e05"
DB_MARKETING = "ad8ed25d26f04c4c93f7683c8c472cf2"
DB_CLIENT_DIRECTORY = "b584e60fb3cf460cbd3f2b18c573a655"
DB_BRAND_ASSETS = "fd6384b95615444c81024027afb75416"  # Corrected from hierarchy
DB_SOCIAL_CONTENT = "bd1713b0042c435abe19365b0eb60752"  # Corrected from hierarchy
DB_LEARNING = "856d411b9a2245bab498a6d9204f8f59"  # Corrected
DB_EMAIL_CAMPAIGNS = "ab753e27f8774a17aee5ac2b9b9f39e3"  # Corrected
DB_COMPETITIVE_ANALYSIS = "4a4fa457b88042d48929af19aa2fdbb5"  # Corrected
DB_KPI_GOALS = "ece92262d9ab433783c4271a484a0875"  # Corrected
DB_LEAD_GEN = "be3a6bdbf8524dca9d23ed69b66c8f52"  # Corrected
DB_TEAM_CONTRACTORS = "17f6d28c684c4edf8aa045f4c114230e"  # New mapped
DB_EQUIPMENT = "6bf3b73a9a2d40be9c5e0a90d8ea03f7"  # New mapped

# User Provided Pages (Potential Parents or DBs)
PAGE_COMPANY_INFO = "316ef0a11a7346dfa13510c5572f154e"
PAGE_PHOTO_PRODUCTION = "4f5d21bd339449b19ac2ac3413782481"
PAGE_BIZ_OPS = "900a7f1e373b45189995e1d48c59f832"
PAGE_FINANCIAL = "a94d93efdb894ba980a921bb40e33ffd"
PAGE_MARKETING_SALES = "9f69f86af96e4c938a0137ef7a22fd86"
PAGE_TECHNICAL_DEV = "ffaf9d964d5e4ec282f174a97a5e4827"
PAGE_TEAM_RESOURCES = "f1b8f2adaa6d4285bb1907146a73e966"


class NotionSkill:
    def __init__(self, token: Optional[str] = None):
        # Use provided token or fallback to Who Visions secret from env
        self.token = (
            token
            or os.environ.get("NOTION_WHO_VISIONS_SECRET")
            or os.environ.get("NOTION_OBSERVATORY_SECRET")
        )
        if not self.token:
            # Try the main token if observatory is missing
            self.token = os.environ.get("NOTION_WHO_VISIONS_SECRET")

        if self.token:
            self.client = Client(auth=self.token)
        else:
            print("⚠️ Notion Token not found. NotionSkill operating in limited mode.")
            self.client = None

    def _get_db_id_for_type(self, project_type: str) -> str:
        """Determines the correct database ID based on project type."""
        pt = project_type.lower()
        if "web" in pt or "dev" in pt:
            return DB_WEB_PROJECTS
        elif "photo" in pt or "shoot" in pt:
            return DB_PHOTO_PROJECTS
        elif "task" in pt or "component" in pt:
            return DB_PROJECT_TRACKER
        elif "marketing" in pt:
            return DB_MARKETING
        elif "social" in pt:
            return DB_SOCIAL_CONTENT
        elif "brand" in pt:
            return DB_BRAND_ASSETS
        elif "email" in pt:
            return DB_EMAIL_CAMPAIGNS
        elif "learn" in pt:
            return DB_LEARNING
        elif "comp" in pt:
            return DB_COMPETITIVE_ANALYSIS
        elif "kpi" in pt:
            return DB_KPI_GOALS
        elif "lead" in pt:
            return DB_LEAD_GEN
        return DB_PROJECT_TRACKER  # Default

    def create_project(
        self, name: str, project_type: str, status: str = "Not Started"
    ) -> Dict[str, Any]:
        """Creates a new project in the appropriate Notion database."""
        if not self.client:
            return {"error": "Notion client not initialized"}

        db_id = self._get_db_id_for_type(project_type)

        try:
            properties = {
                "Name": {"title": [{"text": {"content": name}}]},
                "Status": {"select": {"name": status}},
                "Type": {"select": {"name": project_type}},
                "Created At": {"date": {"start": datetime.utcnow().isoformat()}}
            }
            response = self.client.pages.create(
                parent={"database_id": db_id},
                properties=properties
            )
            return {"status": "success", "page_id": response["id"], "url": response.get("url")}
        except APIResponseError as e:
            return {"status": "error", "message": str(e)}

    def search_observatory(self, query: str) -> List[Dict[str, Any]]:
        """Searches across all accessible Notion databases."""
        if not self.client:
            return []

        try:
            response = self.client.search(
                query=query,
                filter={"value": "page", "property": "object"},
                page_size=5
            )
            return [
                {
                    "id": page["id"],
                    "title": self._extract_title(page),
                    "url": page.get("url"),
                    "last_edited": page.get("last_edited_time")
                }
                for page in response.get("results", [])
            ]
        except Exception as e:  # pylint: disable=W0718
            print(f"Search failed: {e}")
            return []

    def log_training_metric(
        self,
        # Identification
        model_name: str = "Unknown",
        run_id: str = "N/A",
        session_id: str = "N/A",
        user_id: str = "N/A",
        request_id: str = "N/A",
        endpoint: str = "N/A",

        # Performance
        latency: float = 0.0,
        duration: float = 0.0,
        response_code: int = 200,

        # Costs
        token_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,

        # Status & Feedback
        success: bool = True,
        error_message: str = "",
        environment: str = "Dev",
        feedback: str = "",
        rating: int = 0
    ) -> bool:
        """Logs a comprehensive AI metric to the Metrics Log database."""
        if not self.client:
            print("Error: Client not initialized.")
            return False

        try:
            # Construct standard properties payload based on User Verified Schema
            properties = {
                # Title: Name
                "Name": {"title": [{"text": {"content": f"{model_name} - Log"}}]},

                # Text Fields
                "Model Name": {"rich_text": [{"text": {"content": model_name}}]},
                "Session ID": {"rich_text": [{"text": {"content": session_id}}]},
                "Run ID": {"rich_text": [{"text": {"content": run_id}}]},
                "User ID": {"rich_text": [{"text": {"content": user_id}}]},

                # Selects
                "Environment": {"select": {"name": environment}},

                # Dates
                "Date": {"date": {"start": datetime.utcnow().isoformat()}},

                # Metrics (Numbers)
                "Latency": {"number": float(latency)},
                "Cost": {"number": float(cost)},
                "Token Count": {"number": int(token_count)},

                # Status
                "Success": {"checkbox": success},
            }

            # Conditional Number Fields (Map only if non-zero to avoid clutter, or always?)
            # User list says they EXIST, so we map them directly.
            if input_tokens:
                properties["Input Tokens"] = {"number": int(input_tokens)}
            if output_tokens:
                properties["Output Tokens"] = {"number": int(output_tokens)}
            if duration:
                properties["Duration"] = {"number": float(duration)}
            if response_code:
                properties["Response Code"] = {"number": int(response_code)}

            # Optional Text Fields
            if request_id != "N/A":
                properties["Request ID"] = {"rich_text": [{"text": {"content": request_id}}]}
            if endpoint != "N/A":
                properties["Endpoint"] = {"rich_text": [{"text": {"content": endpoint}}]}
            if error_message:
                properties["Error Message"] = {"rich_text": [{"text": {"content": error_message}}]}
            if feedback:
                properties["Feedback"] = {"rich_text": [{"text": {"content": feedback}}]}

            # Number mapping
            if input_tokens:
                properties["Input Tokens"] = {"number": int(input_tokens)}
            if output_tokens:
                properties["Output Tokens"] = {"number": int(output_tokens)}
            if duration:
                properties["Duration"] = {"number": float(duration)}
            if response_code:
                properties["Response Code"] = {"number": int(response_code)}
            if rating:
                properties["Rating"] = {"number": int(rating)}

            # Actually create the page in Notion
            self.client.pages.create(
                parent={"database_id": DB_METRICS_LOG},
                properties=properties
            )
            return True
        except APIResponseError as e:
            print(f"Error logging metric: {e}")
            raise e
        except Exception as e:  # pylint: disable=W0718
            print(f"Unexpected error: {e}")
            return False

    # --- MCP: Content Tools ---
    def fetch_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieves content from a Notion page (notion-fetch)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            page = self.client.pages.retrieve(page_id)
            blocks = self.client.blocks.children.list(page_id)
            return {"page": page, "content": blocks.get("results", [])}
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    def create_page(
        self,
        parent_id: str,
        title: str,
        properties: Dict[str, Any] = None,
        children: List[Dict] = None
    ) -> Dict[str, Any]:
        """Creates a new Notion page (notion-create-pages)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            # Determine parent type (database or page)
            # Simple heuristic: if parent_id has dashes, assume page/db ID.
            # API requires specific parent object.
            # Try as page first, if fails, might be database?
            # User usually supplies ID. Default to page_id.
            # For simplicity in this tool, we assume parent is a page or db id.

            is_page = "-" in parent_id
            parent_type = {"page_id": parent_id} if is_page else {"database_id": parent_id}
            payload = {
                "parent": parent_type,
                "properties": properties or {},
                "children": children or []
            }

            # Helper for title if generic properties passed
            if not properties and title:
                payload["properties"] = {"title": [{"text": {"content": title}}]}
            elif title and "Name" in (properties or {}):  # Common CSV case
                pass  # User handled it
            elif title:
                # Try to guess title property name? usually "title" or "Name"
                # For page parent, title property is 'title'.
                payload["properties"]["title"] = [{"text": {"content": title}}]

            return self.client.pages.create(**payload)
        except Exception as e:  # pylint: disable=W0718
            # Fallback: try database parent
            try:
                payload["parent"] = {"database_id": parent_id}
                return self.client.pages.create(**payload)
            except Exception as e2:  # pylint: disable=W0718
                return {"error": f"Failed as page: {e}. Failed as db: {e2}"}

    def update_page(
        self, page_id: str, properties: Dict[str, Any] = None, archived: bool = False
    ) -> Dict[str, Any]:
        """Updates a page's properties or status (notion-update-page)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            kwargs = {}
            if properties:
                kwargs["properties"] = properties
            if archived:
                kwargs["archived"] = True
            return self.client.pages.update(page_id, **kwargs)
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    def move_page(self, page_id: str, new_parent_id: str) -> Dict[str, Any]:
        """Moves a page to a new parent (notion-move-pages)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            # Moving is just updating the parent, but API restricts moving via update endpoint sometimes?
            # Actually, API allows updating `parent` property? No, it's restricted.
            # Notion API docs say: "The parent parameter cannot be updated" for pages.
            # WORKAROUND: We can't actually move via API easily.
            # Wait, the prompt says "notion-move-pages".
            # MCP might implemented it via "Permissions" or "Structure".
            # Actually, standard Notion API *does not* support moving pages via PATCH.
            return {"error": "Notion API does not support moving pages via API yet."}
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    # --- MCP: Database Tools ---
    def create_database(
        self, parent_page_id: str, title: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a new database (notion-create-database)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            return self.client.databases.create(
                parent={"page_id": parent_page_id},
                title=[{"text": {"content": title}}],
                properties=properties
            )
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    def update_database(
        self,
        database_id: str,
        title: str = None,
        properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Updates a database schema (notion-update-database)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            kwargs = {}
            if title:
                kwargs["title"] = [{"text": {"content": title}}]
            if properties:
                kwargs["properties"] = properties
            return self.client.databases.update(database_id, **kwargs)
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    def query_database(
        self, database_id: str, filter: Dict = None, sort: List = None
    ) -> List[Dict]:
        """Queries a database (notion-query-data-sources)."""
        if not self.client:
            return []
        try:
            kwargs = {"database_id": database_id}
            if filter:
                kwargs["filter"] = filter
            if sort:
                kwargs["sorts"] = sort

            res = self.client.databases.query(**kwargs)
            return res.get("results", [])
        except Exception as e:  # pylint: disable=W0718
            print(f"Query failed: {e}")
            return []

    # --- MCP: Collaboration Tools ---
    def create_comment(self, page_id: str, text: str) -> Dict[str, Any]:
        """Adds a comment to a page (notion-create-comment)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            return self.client.comments.create(
                parent={"page_id": page_id},
                rich_text=[{"text": {"content": text}}]
            )
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    def get_comments(self, page_id: str) -> List[Dict]:
        """Lists comments for a page (notion-get-comments)."""
        if not self.client:
            return []
        try:
            res = self.client.comments.list(block_id=page_id)
            return res.get("results", [])
        except Exception as e:  # pylint: disable=W0718
            return [{"error": str(e)}]

    def get_users(self) -> List[Dict]:
        """Lists all users (notion-get-users)."""
        if not self.client:
            return []
        try:
            res = self.client.users.list()
            return res.get("results", [])
        except Exception as e:  # pylint: disable=W0718
            return [{"error": str(e)}]

    def get_me(self) -> Dict[str, Any]:
        """Get bot user info (notion-get-self)."""
        if not self.client:
            return {}
        try:
            return self.client.users.me()
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    # --- MCP: Advanced / Deep Dive ---
    def duplicate_page(self, page_id: str) -> Dict[str, Any]:
        """Duplicates a page (notion-duplicate-page) by copying properties and content."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            # 1. Fetch source
            original = self.client.pages.retrieve(page_id)
            blocks = self.client.blocks.children.list(page_id).get("results", [])

            # 2. Prepare new payload
            _props = original.get("properties", {})  # Reserved for future detailed copy
            # We can't copy status/created_time/rollup usually.
            # Simplified: just copy Name/Title and try to reuse parent.
            parent = original.get("parent")

            # Clean properties (remove readonly fields ideally, but for now just try basic)
            # Actually, standard properties like 'Status' might be read-only in some contexts?
            # Safer to just copy Title.
            title = self._extract_title(original)
            new_props = {"Name": {"title": [{"text": {"content": f"Copy of {title}"}}]}}

            # 3. Create
            new_page = self.client.pages.create(
                parent=parent,
                properties=new_props
            )
            new_id = new_page["id"]

            # 4. Copy Blocks (append children)
            # Need to clean blocks (remove IDs).
            clean_blocks = []
            for b in blocks:
                if "id" in b:
                    del b["id"]
                if "parent" in b:
                    del b["parent"]
                if "created_time" in b:
                    del b["created_time"]
                if "last_edited_time" in b:
                    del b["last_edited_time"]
                if "created_by" in b:
                    del b["created_by"]
                if "last_edited_by" in b:
                    del b["last_edited_by"]
                # Can't copy nested children easily
                if "has_children" in b:
                    del b["has_children"]
                if "archived" in b:
                    del b["archived"]
                if "type" in b:
                    clean_blocks.append(b)

            if clean_blocks:
                self.client.blocks.children.append(new_id, children=clean_blocks)

            return {"status": "success", "new_page_id": new_id, "url": new_page.get("url")}
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Retrieves a specific user (notion-get-user)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            return self.client.users.retrieve(user_id)
        except Exception as e:  # pylint: disable=W0718
            return {"error": str(e)}

    def get_teams(self) -> List[Dict]:
        """Retrieves teams (notion-get-teams). Note: APIs mostly return empty for non-Enterprise."""
        # Using search as proxy or just empty list as this endpoints is often restricted
        return []

    # Update move_page with attempt logic
    def move_page_advanced(self, page_id: str, new_parent_page_id: str) -> Dict[str, Any]:
        """Attempts to move a page via update (notion-move-pages)."""
        if not self.client:
            return {"error": "Client not initialized"}
        try:
            return self.client.pages.update(
                page_id,
                parent={"page_id": new_parent_page_id}
            )
        except APIResponseError as e:
            return {"error": f"Move failed (API Limitation?): {e}"}

    def _extract_title(self, page: Dict[str, Any]) -> str:
        """Helper to safely extract page title."""
        props = page.get("properties", {})
        # Try common title fields
        for key in ["Name", "Title", "Page", "Task"]:
            if key in props and props[key]["id"] == "title":
                title_list = props[key].get("title", [])
                if title_list:
                    return title_list[0].get("text", {}).get("content", "Untitled")
        return "Untitled"
