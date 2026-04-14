#!/usr/bin/env node

const axios = require('axios');

// Configuration
const API_URL = "https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr/api";
const API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MmMzYTg1Ny0yZjY3LTQ3NWQtYjNlYi1jMTg4MGJhN2NjOGIiLCJleHAiOjE3NzUxMjU5OTAsImlzcyI6Im1lYWxpZSJ9.L_Ig2zGzmH0xyDLm4N3O3aTUOhNsrbDklJYnytFt2PY";
const COOKBOOK_ID = "20afabc1-5185-4f9b-a6d9-2a416b85786c";

const headers = {
    "Authorization": `Bearer ${API_TOKEN}`,
    "Content-Type": "application/json"
};

// Tools
const tools = [
    {
        name: "list_recipes",
        description: "Liste toutes les recettes dans Mealie",
        inputSchema: {
            type: "object",
            properties: {
                page: { type: "integer", default: 1 },
                per_page: { type: "integer", default: 20 }
            }
        }
    },
    {
        name: "get_import_ia_status",
        description: "Affiche le statut du cookbook Import IA",
        inputSchema: { type: "object", properties: {} }
    },
    {
        name: "organize_import_ia",
        description: "Organise les recettes Import IA dans le cookbook",
        inputSchema: { type: "object", properties: {} }
    },
    {
        name: "search_recipes",
        description: "Recherche des recettes dans Mealie",
        inputSchema: {
            type: "object",
            properties: {
                query: { type: "string" },
                page: { type: "integer", default: 1 },
                per_page: { type: "integer", default: 20 }
            },
            required: ["query"]
        }
    },
    {
        name: "scrape_recipe",
        description: "Scrape une recette depuis une URL",
        inputSchema: {
            type: "object",
            properties: {
                url: { type: "string" }
            },
            required: ["url"]
        }
    }
];

// Tool functions
async function listRecipes(page = 1, per_page = 20) {
    try {
        const response = await axios.get(`${API_URL}/recipes`, {
            params: { page, perPage: per_page },
            headers
        });
        
        if (response.status === 200) {
            const data = response.data;
            const recipes = data.items || [];
            const total = data.total || 0;
            
            let result = `📋 Liste des recettes (${total} totales):\n`;
            recipes.forEach(recipe => {
                result += `• ${recipe.name} (slug: ${recipe.slug})\n`;
            });
            
            return result.trim();
        } else {
            return `❌ Erreur: ${response.status}`;
        }
    } catch (error) {
        return `❌ Exception: ${error.message}`;
    }
}

async function getImportIAStatus() {
    try {
        const response = await axios.get(`${API_URL}/households/cookbooks/${COOKBOOK_ID}`, { headers });
        
        if (response.status === 200) {
            const cookbook = response.data;
            const recipes = cookbook.recipes || [];
            
            // Compter les recettes IA
            const allRecipesResponse = await axios.get(`${API_URL}/recipes?perPage=200`, { headers });
            let iaCount = 0;
            if (allRecipesResponse.status === 200) {
                const allRecipes = allRecipesResponse.data.items || [];
                iaCount = allRecipes.filter(recipe => {
                    const name = recipe.name.toLowerCase();
                    return [
                        "(1)", "(2)", "sauce-tomate", "salade-de-brocoli", "riz-frit",
                        "cafe-glace", "saumon-grille", "rouleaux", "tartelettes",
                        "choux-de-bruxelles", "chou-rave", "hot-dogs", "bacon-glace",
                        "relish-de-mais", "choux-a-la-creme", "tarte-a-la-mangue",
                        "casserole-de-poisson", "biscuits-boule", "legumes-fondants"
                    ].some(indicator => name.includes(indicator));
                }).length;
            }
            
            const taux = iaCount > 0 ? (recipes.length / iaCount * 100) : 0;
            
            return `📚 COOKBOOK 'IMPORT IA'
📝 Nom: ${cookbook.name}
📄 Description: ${cookbook.description}
🔖 Slug: ${cookbook.slug}
📊 Recettes organisées: ${recipes.length}

🤖 Recettes Import IA totales: ${iaCount}
📊 Taux d'organisation: ${taux.toFixed(1)}%`;
        } else {
            return `❌ Erreur: ${response.status}`;
        }
    } catch (error) {
        return `❌ Exception: ${error.message}`;
    }
}

async function organizeImportIA() {
    try {
        const response = await axios.get(`${API_URL}/recipes?perPage=200`, { headers });
        if (response.status !== 200) {
            return `❌ Erreur récupération recettes: ${response.status}`;
        }
        
        const allRecipes = response.data.items || [];
        
        // Identifier les recettes IA
        const iaRecipes = [];
        allRecipes.forEach(recipe => {
            const name = recipe.name.toLowerCase();
            if ([
                "(1)", "(2)", "sauce-tomate", "salade-de-brocoli", "riz-frit",
                "cafe-glace", "saumon-grille", "rouleaux", "tartelettes",
                "choux-de-bruxelles", "chou-rave", "hot-dogs", "bacon-glace",
                "relish-de-mais", "choux-a-la-creme", "tarte-a-la-mangue",
                "casserole-de-poisson", "biscuits-boule", "legumes-fondants"
            ].some(indicator => name.includes(indicator))) {
                iaRecipes.push({ id: recipe.id });
            }
        });
        
        // Mettre à jour le cookbook
        const updateData = {
            name: "Import IA",
            description: "Recettes importees automatiquement par l IA",
            slug: "import-ia-1",
            position: 1,
            public: false,
            queryFilterString: "",
            recipes: iaRecipes
        };
        
        const updateResponse = await axios.put(`${API_URL}/households/cookbooks/${COOKBOOK_ID}`, updateData, { headers });
        
        if (updateResponse.status === 200) {
            return `✅ ${iaRecipes.length} recettes organisées dans Import IA`;
        } else {
            return `❌ Erreur mise à jour: ${updateResponse.status}`;
        }
    } catch (error) {
        return `❌ Exception: ${error.message}`;
    }
}

async function searchRecipes(query, page = 1, per_page = 20) {
    try {
        const response = await axios.get(`${API_URL}/recipes`, {
            params: { search: query, page, perPage: per_page },
            headers
        });
        
        if (response.status === 200) {
            const data = response.data;
            const recipes = data.items || [];
            const total = data.total || 0;
            
            let result = `🔍 Résultats pour '${query}' (${total} totaux):\n`;
            recipes.forEach(recipe => {
                result += `• ${recipe.name} (slug: ${recipe.slug})\n`;
            });
            
            return result.trim();
        } else {
            return `❌ Erreur: ${response.status}`;
        }
    } catch (error) {
        return `❌ Exception: ${error.message}`;
    }
}

async function scrapeRecipe(url) {
    try {
        const scrapeData = { url };
        const response = await axios.post(`${API_URL}/recipes/create/url`, scrapeData, { headers });
        
        if (response.status === 201) {
            const slug = response.data || response.text;
            return `✅ Recette scrapée avec succès! Slug: ${slug}`;
        } else {
            return `❌ Erreur scraping: ${response.status}`;
        }
    } catch (error) {
        return `❌ Exception: ${error.message}`;
    }
}

// Tool mapping
const toolFunctions = {
    list_recipes: (args) => listRecipes(args.page, args.per_page),
    get_import_ia_status: (args) => getImportIAStatus(),
    organize_import_ia: (args) => organizeImportIA(),
    search_recipes: (args) => searchRecipes(args.query, args.page, args.per_page),
    scrape_recipe: (args) => scrapeRecipe(args.url)
};

// MCP Server implementation
let initialized = false;

async function handleRequest(request) {
    const method = request.method;
    
    if (method === "initialize") {
        initialized = true;
        return {
            jsonrpc: "2.0",
            id: request.id,
            result: {
                protocolVersion: "2024-11-05",
                capabilities: { tools: {} },
                serverInfo: { name: "mealie-mcp", version: "1.0.0" }
            }
        };
    }
    
    if (method === "tools/list" && initialized) {
        return {
            jsonrpc: "2.0",
            id: request.id,
            result: { tools }
        };
    }
    
    if (method === "tools/call" && initialized) {
        const name = request.params.name;
        const arguments = request.params.arguments || {};
        
        if (toolFunctions[name]) {
            try {
                const result = await toolFunctions[name](arguments);
                return {
                    jsonrpc: "2.0",
                    id: request.id,
                    result: { content: [{ type: "text", text: result }] }
                };
            } catch (error) {
                return {
                    jsonrpc: "2.0",
                    id: request.id,
                    error: { code: -32603, message: `Erreur: ${error.message}` }
                };
            }
        } else {
            return {
                jsonrpc: "2.0",
                id: request.id,
                error: { code: -32601, message: `Outil inconnu: ${name}` }
            };
        }
    }
    
    return {
        jsonrpc: "2.0",
        id: request.id,
        error: { code: -32601, message: `Méthode inconnue: ${method}` }
    };
}

// Main server loop
async function main() {
    process.stdin.setEncoding('utf8');
    let buffer = '';
    
    for await (const chunk of process.stdin) {
        buffer += chunk;
        
        // Process each complete JSON line
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer
        
        for (const line of lines) {
            if (line.trim()) {
                try {
                    const request = JSON.parse(line.trim());
                    const response = await handleRequest(request);
                    console.log(JSON.stringify(response));
                } catch (error) {
                    const errorResponse = {
                        jsonrpc: "2.0",
                        id: null,
                        error: { code: -32603, message: `Erreur serveur: ${error.message}` }
                    };
                    console.log(JSON.stringify(errorResponse));
                }
            }
        }
    }
}

if (require.main === module) {
    main().catch(console.error);
}
