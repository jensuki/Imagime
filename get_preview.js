require('dotenv').config();

// Use the same credentials as the Python app unless Node-specific ones are set.
if (!process.env.SPOTIFY_CLIENT_ID && process.env.SPOT_CLIENT_ID) {
    process.env.SPOTIFY_CLIENT_ID = process.env.SPOT_CLIENT_ID;
}
if (!process.env.SPOTIFY_CLIENT_SECRET && process.env.SPOT_API_KEY) {
    process.env.SPOTIFY_CLIENT_SECRET = process.env.SPOT_API_KEY;
}

const spotifyPreviewFinder = require('spotify-preview-finder');

const query = process.argv[2];

// run search + print out the results as JSON for python to read
async function run() {
    try {
        // search spotify using provided query
        const result = await spotifyPreviewFinder(query, 1);

        // if songs are found with preview_url, send back first result
        if (result.success && result.results.length > 0) {
            const song = result.results[0];
            const response = {
                name: song.name,
                spotifyUrl: song.spotifyUrl,
                previewUrls: song.previewUrls
            }
            console.log(JSON.stringify(response));  // what python will parse
        } else {
            console.log(JSON.stringify({ previewUrls: [], error: result.error || 'No preview found' }))
        }
    } catch (err) {
        // if error
        console.log(JSON.stringify({ error: err.message }));
    }
}

run()
