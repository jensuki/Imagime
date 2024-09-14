document.addEventListener('DOMContentLoaded', function () {
    const loadMoreButton = document.getElementById('load-more-button');
    const songList = document.getElementById('song-list');
    let offset = loadMoreButton ? parseInt(loadMoreButton.getAttribute('data-offset')) : 0;
    const postId = loadMoreButton ? loadMoreButton.getAttribute('data-post-id') : null;

    const image_form = document.getElementById('image_form');
    const spinner = document.getElementById('loading-spinner');

    // event listener for image form
    if (image_form) {
        image_form.addEventListener('submit', function (event) {
            event.preventDefault();  // Prevent the default form submission for image_form only

            // show the spinner
            spinner.style.display = 'block';

            const submitButton = image_form.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            document.querySelector('.add_message').style.display = 'none';
            image_form.style.display = 'none';

            // submit form after showing the spinner / hiding elements
            image_form.submit();
        });
    }

    // custom audio controls

    let currentAudio = null;
    let currentButton = null;

    // Function to play/pause the audio
    function togglePlay(button) {
        const audioUrl = button.getAttribute('data-audio');
        const progressBar = button.closest('.audio-player').querySelector('.progress-bar');

        // Pause the current track if a new one is played
        if (currentAudio && currentAudio.src !== audioUrl) {
            currentAudio.pause();
            currentButton.innerHTML = '<i class="fa fa-play"></i>';
        }

        if (!currentAudio || currentAudio.src !== audioUrl) {
            currentAudio = new Audio(audioUrl);
            currentButton = button;
            currentAudio.play();
            button.innerHTML = '<i class="fa fa-pause"></i>';

            currentAudio.addEventListener('timeupdate', () => {
                const percentage = (currentAudio.currentTime / currentAudio.duration) * 100;
                progressBar.style.width = `${percentage}%`;
            });

            currentAudio.addEventListener('ended', () => {
                button.innerHTML = '<i class="fa fa-play"></i>';
                progressBar.style.width = '0%';
            });

        } else if (currentAudio.paused) {
            currentAudio.play();
            button.innerHTML = '<i class="fa fa-pause"></i>';
        } else {
            currentAudio.pause();
            button.innerHTML = '<i class="fa fa-play"></i>';
        }
    }


    // Function to attach the play/pause event listeners
    function attachPlayListeners() {
        document.querySelectorAll('.play-btn').forEach(button => {
            button.onclick = () => togglePlay(button);
        });
    }

    // Handle favorite toggle
    async function handleFavoriteToggle(evt) {
        evt.preventDefault();
        const form = evt.target;
        const button = form.querySelector('.favorite-btn');
        const icon = button.querySelector('i');
        const formData = new FormData(form);

        try {
            const response = await axios.post(form.action, formData);
            if (response.status === 200) {
                icon.classList.toggle('fas');
                icon.classList.toggle('far');
            }
        } catch (error) {
            console.error("Error toggling favorite:", error);
        }
    }

    // Attach listeners for favorite toggle
    function attachFavoriteListeners() {
        document.querySelectorAll('.favorite-form').forEach(form => {
            form.addEventListener('submit', handleFavoriteToggle);
        });
    }

    // Handle removing favorites
    async function handleRemoveFavorite(evt) {
        evt.preventDefault();
        const form = evt.target;
        const li = form.closest('li');

        try {
            const response = await axios.post(form.action);
            if (response.status === 200) {
                li.remove();
            }
        } catch (error) {
            console.error("Error removing favorite:", error);
        }
    }

    // Attach listeners for removing favorites
    function attachRemoveFavoriteListeners() {
        document.querySelectorAll('.remove-favorite-form').forEach(form => {
            form.addEventListener('submit', handleRemoveFavorite);
        });
    }

    // Handle the public/private toggle for favorites
    async function handleFavoritesVisibilityToggle(evt) {
        const form = evt.target.closest('form');
        const formData = new FormData(form);

        try {
            await axios.post(form.action, formData);
        } catch (error) {
            console.error('Error updating favorites visibility:', error);
        }
    }

    // Attach listener for public/private favorites toggle
    function attachFavoritesVisibilityListener() {
        const favoritesCheckbox = document.getElementById('favoritesVisibility');
        if (favoritesCheckbox) {
            favoritesCheckbox.addEventListener('change', handleFavoritesVisibilityToggle);
        }
    }

    // Function to load more songs via Axios
    function loadMoreSongs() {
        axios.get(`/posts/${postId}?offset=${offset}&json=true`)
            .then(response => {
                const data = response.data;

                if (data.songs.length > 0) {
                    data.songs.forEach(song => {
                        const li = document.createElement('li');
                        li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center', 'custom-audio-item');
                        li.innerHTML = `
                        <div class="d-flex align-items-center" style="flex-grow: 1;">
                            <img src="${song.image_url}" alt="Album Cover" style="width: 50px; height: 50px; margin-right: 15px;">
                            <div>
                                <p class="mb-1">
                                    <a href="${song.spotify_url}" style="text-decoration: none; color: inherit;" target="_blank">
                                        ${song.title} by ${song.artist}
                                    </a>
                                </p>
                                <div class="audio-player">
                                    <button class="play-btn" data-audio="${song.preview_url}">
                                        <i class="fa fa-play"></i>
                                    </button>
                                    <div class="progress">
                                        <div class="progress-bar"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <form class="favorite-form" style="margin-left: auto;" action="/posts/${postId}/songs/${song.id}/favorite" method="POST">
                            <button type="submit" class="favorite-btn">
                                <i class="${song.is_favorited ? 'fas fa-heart' : 'far fa-heart'}"></i>
                            </button>
                        </form>
                    `;
                        songList.appendChild(li);
                    });

                    attachPlayListeners();
                    attachFavoriteListeners();
                    attachRemoveFavoriteListeners();

                    offset += data.songs.length;
                    if (loadMoreButton) {
                        loadMoreButton.setAttribute('data-offset', offset);
                    }
                } else {
                    loadMoreButton.remove();
                }
            });
    }

    // Trigger load more on click
    if (loadMoreButton) {
        loadMoreButton.addEventListener('click', loadMoreSongs);
    }

    // Attach initial listeners
    attachPlayListeners();
    attachFavoriteListeners();
    attachRemoveFavoriteListeners();
    attachFavoritesVisibilityListener();
});
