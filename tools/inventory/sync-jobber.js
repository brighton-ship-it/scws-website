#!/usr/bin/env node
/**
 * Sync products from Jobber API to local inventory
 * Run: node sync-jobber.js
 */

const fs = require('fs');
const path = require('path');

const CREDS_FILE = '/Users/jarvis/clawd/jobber_credentials.json';
const OUTPUT_FILE = path.join(__dirname, 'products.json');

async function refreshToken(creds) {
    const params = new URLSearchParams({
        client_id: creds.client_id,
        client_secret: creds.client_secret,
        grant_type: 'refresh_token',
        refresh_token: creds.refresh_token
    });

    const resp = await fetch('https://api.getjobber.com/api/oauth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params
    });

    const data = await resp.json();
    if (data.access_token) {
        creds.access_token = data.access_token;
        creds.refresh_token = data.refresh_token;
        creds.token_updated_at = new Date().toISOString();
        fs.writeFileSync(CREDS_FILE, JSON.stringify(creds, null, 2));
        console.log('✓ Token refreshed');
    }
    return creds;
}

async function fetchAllProducts(accessToken) {
    const products = [];
    let cursor = null;
    let page = 1;

    while (true) {
        const query = `{
            productOrServices(first: 100${cursor ? `, after: "${cursor}"` : ''}) {
                nodes {
                    id
                    name
                    description
                    defaultUnitCost
                    internalUnitCost
                    category
                    visible
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }`;

        const resp = await fetch('https://api.getjobber.com/api/graphql', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
                'X-JOBBER-GRAPHQL-VERSION': '2025-04-16'
            },
            body: JSON.stringify({ query })
        });

        const data = await resp.json();
        
        if (data.errors) {
            throw new Error(data.errors[0].message);
        }

        const nodes = data.data.productOrServices.nodes;
        products.push(...nodes);
        console.log(`  Page ${page}: ${nodes.length} products (total: ${products.length})`);

        if (!data.data.productOrServices.pageInfo.hasNextPage) break;
        cursor = data.data.productOrServices.pageInfo.endCursor;
        page++;
    }

    return products;
}

async function main() {
    console.log('🔄 Syncing products from Jobber...\n');

    let creds = JSON.parse(fs.readFileSync(CREDS_FILE, 'utf8'));

    // Try with current token, refresh if expired
    try {
        const testResp = await fetch('https://api.getjobber.com/api/graphql', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${creds.access_token}`,
                'Content-Type': 'application/json',
                'X-JOBBER-GRAPHQL-VERSION': '2025-04-16'
            },
            body: JSON.stringify({ query: '{ account { name } }' })
        });
        const testData = await testResp.json();
        if (testData.message === 'Access token expired') {
            creds = await refreshToken(creds);
        }
    } catch (e) {
        creds = await refreshToken(creds);
    }

    const products = await fetchAllProducts(creds.access_token);

    // Load existing inventory data if it exists
    let existingInventory = {};
    const inventoryFile = path.join(__dirname, 'inventory.json');
    if (fs.existsSync(inventoryFile)) {
        const inv = JSON.parse(fs.readFileSync(inventoryFile, 'utf8'));
        inv.items.forEach(item => {
            existingInventory[item.jobberId] = item;
        });
    }

    // Merge: keep inventory counts, update product info from Jobber
    const items = products
        .filter(p => p.visible !== false) // Only visible products
        .map(p => {
            const existing = existingInventory[p.id] || {};
            return {
                jobberId: p.id,
                name: p.name,
                description: p.description || '',
                cost: p.defaultUnitCost || 0,
                internalCost: p.internalUnitCost || 0,
                category: p.category,
                // Preserve inventory data if exists
                warehouse: existing.warehouse ?? 0,
                truck: existing.truck ?? 0,
                minStock: existing.minStock ?? 0,
                lastUpdated: existing.lastUpdated || null
            };
        })
        .sort((a, b) => a.name.localeCompare(b.name));

    const output = {
        syncedAt: new Date().toISOString(),
        source: 'Jobber API',
        count: items.length,
        items
    };

    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
    console.log(`\n✅ Synced ${items.length} products to ${OUTPUT_FILE}`);

    // Also save inventory file if it doesn't exist
    if (!fs.existsSync(inventoryFile)) {
        fs.writeFileSync(inventoryFile, JSON.stringify(output, null, 2));
        console.log(`✅ Created initial inventory.json`);
    }
}

main().catch(console.error);
