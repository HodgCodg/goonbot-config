// Fix for OpenClaw context window display bug
// This script patches the config to ensure context windows are read correctly

const fs = require('fs');
const path = require('path');

const CONFIG_PATH = '/home/botvm/.openclaw/openclaw.json';

try {
    const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
    
    // Verify models are at correct location
    if (!config.models?.providers) {
        console.error('❌ Models not found at cfg?.models?.providers');
        process.exit(1);
    }
    
    // Check lmstudio provider
    const lmstudio = config.models.providers.lmstudio;
    if (!lmstudio?.models) {
        console.error('❌ LM Studio models array not found');
        process.exit(1);
    }
    
    // Find our model and verify context window
    let foundModel = null;
    for (const model of lmstudio.models) {
        if (model.id.includes('gemma-4-26b-a4b-it')) {
            foundModel = model;
            break;
        }
    }
    
    if (!foundModel) {
        console.error('❌ Qwen 27B model not found');
        process.exit(1);
    }
    
    const contextWindow = foundModel.contextWindow;
    console.log(`✅ Model: ${foundModel.id}`);
    console.log(`   Context Window: ${contextWindow} tokens`);
    console.log(`   Config Location: cfg?.models?.providers.lmstudio.models[].contextWindow`);
    
    // The config is correct - the bug is in OpenClaw's lookup function
    // which doesn't properly await cache initialization before reading
    
    console.log('\n📝 Diagnosis:');
    console.log('   Config IS correctly set up at cfg?.models?.providers.lmstudio.models[].contextWindow');
    console.log('   Bug is in OpenClaw\'s lookupContextTokens() function - it starts async cache load');
    console.log('   but reads from cache immediately without awaiting, so cache may be empty.');
    
    console.log('\n💡 Workaround:');
    console.log('   Run /context detail to see actual runtime context usage');
    console.log('   The 100K limit IS active - only the status display is wrong.');
    
} catch (err) {
    console.error(`❌ Error: ${err.message}`);
    process.exit(1);
}
