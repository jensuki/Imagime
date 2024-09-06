# Imagime

### Imagime enhances music discovery by merging visual content with sound, offering an engaging yet personal way to explore songs that resonate with the images you share.
---
- **Database Schema**: Tables for **[Users] - [Posts] - [Songs] - [PostSongs] - [FavoritedSongs]**

- **Sensitive Information**: *User Account Details* -> Securely store user credentials and profile images. Ensure encryption and safe handling of passwords.
Manage user sessions to prevent unauthorized access. API keys, and tokens need to be securely managed.

- **Functionality**:
    - *Image and Song Integration* -> Users upload an image, which is analyzed to generate keywords that map to related songs from the Spotipy API. These songs are displayed alongside the image. Users can listen to these song previews directly on the app and click on the song to view the full track on Spotipy.

    - *Favorites System* -> Users can favorite songs associated with any post. Favorited songs are stored in the database, and isolated within each user's account. Users have the option to toggle the visibility of their saved songs, allowing them to choose whether their favorited songs are visible to other users or set them as private

    - *Dynamic Content Loading* -> Implemented a "Load More" button to load additional songs and toggle favorites without a full page reload, enhancing user experience.

- **User Flow**:
    - *Sign-Up/Login* -> New users create an account with a username, email, and optional profile image. Existing users log in to access personalized content.

    - *Post Creation* -> Users upload images and optionally add descriptions. The app then matches the image to songs based on generated keywords.

    - *Interaction with Content* -> Users view posts, listen to song previews, and favorite tracks. They can also store songs they like in their favorites page as well as navigate back to the original post that the song was a part of.

- **API Issues**: Handle API responses from Spotipy and Everypixel, ensuring proper error handling and managing edge cases like failed requests or missing data.

- **Workarounds** ->
    - *Handling Post Deletion with Favorited Songs* -> To address the issue where a user deletes a post containing songs that have been favorited by other users, I implemented a solution that preserves the integrity of those favorited songs. When the post is deleted, the reference to the original post is removed, but users who have favorited the songs retain access to them in their favorites list. This ensures that users can still enjoy their saved songs without encountering broken links or missing content.

- **Stretch Goals**:
    - *Custom Playlists* -> Allow users to create playlists based on favorited songs or matched songs from uploaded images.

    - *General* -> Improve song mapping algorithms, expand music sources, add community features, and implement advanced search options.

---

| **Instruction**     | **Description**                                                                                                                                               | **Imagime**                                                                                                                                  |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| **Stack**           | Tech stack used for the project.                                                                                                                               | Python/Flask - PostgreSQL - SQLAlchemy - Jinja - HTML - CSS - JavaScript                                       |
| **Focus**           | Is the front-end UI or the back-end going to be the focus of your project? Or are you going to make an evenly focused full-stack application?                   |magine will be a full-stack application that is a balance of both front-end and back-end elements. - Back-end will support data management & integration with external API’s- Front-end will be focused on creating an engaging intuitive design that will allow users to navigate effortlessly   |
| **Type**            | Will this be a website? A mobile app? Something else?                                                                                                          | Website                                                                                                                                       |
| **Goal**            | What goal will your project be designed to achieve?                                                                                                            | To offer users  an enhanced way to discover music that complements the images they share, creating a unique audio-visual experience. |
| **Users**           | What kind of users will visit your app? In other words, what is the demographic of your users?                                                                  | Music enthusiasts, photographers, and social media users who enjoy discovering new music and pairing it with visual content-- For those seeking an engaging experience without the need for direct interaction with other users                |
| **Data**            | What data do you plan on using? How are you planning on collecting your data?                                                                                  | **Data Sources**: <br>[Spotipy API(with Spotify API)](https://spotipy.readthedocs.io/en/2.24.0/)<br>[Everypixel API](https://labs.everypixel.com/keywording) <br>**Data to Collect**:  API requests to gather song details from Spotipy and image keywords from Everypixel. <br>**Collection Method**: API requests |