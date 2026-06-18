workspace "Code RAG MCP" "Python Code RAG MCP server over RuVector PostgreSQL" {

    !identifiers hierarchical

    model {
        developer = person "Developer" "Uses MCP client to search indexed code"
        cursor = softwareSystem "Cursor IDE" "MCP host for AI-assisted development"

        codeRag = softwareSystem "Code RAG MCP" "Hybrid vector + FTS code search with call-graph context" {
            mcpServer = container "MCP Server" "FastMCP HTTP/stdio transport" "Python 3.12, FastMCP" {
                searchTools = component "Search Tools" "search, call_search, class_search, search_with_context"
                searchService = component "Search Service" "Lane weights, test filters, graph expansion"
                store = component "SQLAlchemy Store" "RuVector SQL queries and connection pool"
            }
            alembic = container "Alembic Migrations" "Schema migrations for code_units/code_edges" "Alembic, SQLAlchemy"
            db = container "RuVector PostgreSQL" "code_units, code_edges, embeddings" "PostgreSQL + RuVector" {
                tags "Database"
            }
        }

        structurizr = softwareSystem "Structurizr" "Architecture documentation" {
            tags "External"
        }

        developer -> cursor "Uses"
        cursor -> codeRag.mcpServer "MCP stdio/HTTP" "Streamable HTTP /mcp"
        codeRag.mcpServer.searchTools -> codeRag.mcpServer.searchService "Invokes"
        codeRag.mcpServer.searchService -> codeRag.mcpServer.store "Queries"
        codeRag.mcpServer.store -> codeRag.db "SQL" "PostgreSQL"
        codeRag.alembic -> codeRag.db "Migrates schema"
        developer -> structurizr "Views C4 diagrams" "HTTP"
    }

    views {
        systemContext codeRag "SystemContext" {
            include *
            autolayout lr
        }

        container codeRag "Containers" {
            include *
            autolayout lr
        }

        component codeRag.mcpServer "Components" {
            include *
            autolayout lr
        }

        styles {
            element "Element" {
                color #0773af
                stroke #0773af
                strokeWidth 7
                shape RoundedBox
            }
            element "Person" {
                shape Person
            }
            element "Database" {
                shape Cylinder
            }
            element "External" {
                background #999999
                color #ffffff
            }
            relationship "Relationship" {
                thickness 4
            }
        }
    }

    configuration {
        scope softwaresystem
    }
}
