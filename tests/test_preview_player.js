const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.join(__dirname, '..');

function player(url, failure) {
    let status;
    const progress = { style: {} };
    const container = {
        querySelector: selector => selector === '.progress-bar' ? progress : status,
        appendChild: element => { status = element; },
    };
    const button = { getAttribute: () => url, closest: () => container };
    const audioInstances = [];
    class Audio {
        constructor(src) {
            this.src = src;
            this.paused = true;
            audioInstances.push(this);
        }
        addEventListener() {}
        async play() {
            if (failure) throw failure;
            this.paused = false;
        }
        pause() { this.paused = true; }
    }
    const document = {
        addEventListener: (name, callback) => callback(),
        getElementById: () => null,
        querySelectorAll: selector => selector === '.play-btn' ? [button] : [],
        createElement: () => ({ setAttribute() {} }),
    };
    vm.runInNewContext(fs.readFileSync(path.join(root, 'static/js/app.js'), 'utf8'), { document, Audio });
    return { button, audioInstances, getStatus: () => status };
}

test('missing previews never create an audio request', () => {
    for (const url of [null, '', 'None', 'null', 'undefined']) {
        const result = player(url);
        assert.equal(result.button.disabled, true);
        assert.equal(result.audioInstances.length, 0);
        assert.match(result.getStatus().textContent, /Preview unavailable/);
    }
});

test('a valid preview plays and pauses', async () => {
    const result = player('https://example.com/preview.mp3');
    await result.button.onclick();
    assert.equal(result.audioInstances[0].paused, false);
    assert.match(result.button.innerHTML, /fa-pause/);
    await result.button.onclick();
    assert.equal(result.audioInstances[0].paused, true);
});

test('playback failure is handled and shown to the user', async () => {
    const result = player('https://example.com/preview.mp3', new Error('Unsupported source'));
    await result.button.onclick();
    assert.equal(result.button.disabled, true);
    assert.match(result.getStatus().textContent, /Preview unavailable/);
});

test('Node helper maps Python credentials and preserves lookup errors', async () => {
    const env = { SPOT_CLIENT_ID: 'test-id', SPOT_API_KEY: 'test-secret' };
    const output = [];
    vm.runInNewContext(fs.readFileSync(path.join(root, 'get_preview.js'), 'utf8'), {
        process: { env, argv: ['node', 'get_preview.js', 'song'] },
        require: name => name === 'dotenv' ? { config() {} } : async () => {
            assert.equal(env.SPOTIFY_CLIENT_ID, 'test-id');
            assert.equal(env.SPOTIFY_CLIENT_SECRET, 'test-secret');
            return { success: false, error: 'Lookup failed', results: [] };
        },
        console: { log: value => output.push(JSON.parse(value)) },
    });
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(output[0].error, 'Lookup failed');
});
