import spotipy
import spotipy.util as util

client_id = "CLIENT ID"
client_secret = "CLIENT SECRET"
redirect_uri = "REDIRECT URL"

username = "USERNAME"
scope = "user-library-read"

token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)

sp = spotipy.Spotify(auth=token)


def compute_similarity(song1, song2):
    similarity = 0
    count = 0
    for feature in song1:
        if feature in song2 and feature != "id" and feature != "uri" and isinstance(song1[feature], (int, float)):
            similarity += abs(float(song1[feature]) - float(song2[feature]))
            count += 1
    return similarity / count


while True:
    song_name = input("Enter the name of a song (Type 'exit' to quit): ")
    if song_name.lower() == "exit":
        break

    results = sp.search(q=song_name, type="track")

    song_id = results["tracks"]["items"][0]["id"]

    recommendations = sp.recommendations(seed_tracks=[song_id])
    recommendation_list = recommendations["tracks"]
    recommendation_list = recommendation_list[:20]
    recommendations["tracks"] = recommendation_list

    popularity = [recommendation["popularity"] for recommendation in recommendations["tracks"]]

    sample_features = sp.audio_features(song_id)[0]
    recommendation_features = sp.audio_features([rec["id"] for rec in recommendations["tracks"]])

    similarities = []
    for recommendation_feature in recommendation_features:
        similarity = compute_similarity(sample_features, recommendation_feature)
        similarities.append(similarity)

    recommendations["tracks"] = [rec for rec in recommendations["tracks"] if
                                 "is_playable" not in rec or rec["is_playable"]]
    recommendations["tracks"] = [x for _, y, x in
                                 sorted(zip(popularity, similarities, recommendations["tracks"]),
                                        key=lambda pair: (pair[0], pair[1]), reverse=True)]
    recommendations["tracks"] = sorted(recommendations["tracks"], key=lambda rec: (
        rec["popularity"], compute_similarity(sample_features, sp.audio_features(rec["id"])[0])), reverse=True)
    num = 1

    track = sp.track(song_id)
    sample_name = track["name"]
    sample_artist = track["artists"][0]["name"]

    print("")
    print(f"Searching for songs like: {sample_name} by {sample_artist}")
    print("")
    similarities = [100 - (similarity / 100) for similarity in similarities]
    similarities = [round(similarity, 2) for similarity in similarities]

    for recommendation in recommendations["tracks"]:
        song_name = recommendation["name"]
        artist = recommendation["artists"][0]["name"]
        popularity = recommendation["popularity"]

        feature = ""
        if len(recommendation["artists"]) > 1:
            feature_artist_names = [artist["name"] for artist in recommendation["artists"][1:]]
            feature = " (ft " + ", ".join(feature_artist_names) + ")"
            if any(name in song_name for name in feature_artist_names):
                feature = ""

        url = recommendation["external_urls"]["spotify"]
        length = recommendation["duration_ms"] / 1000
        minutes, seconds = divmod(length, 60)
        length_str = f"{int(minutes)}:{int(seconds):02d}"
        print(
            f"{num}.) {song_name} - {artist}{feature} ({length_str}): {url} - Popularity: {popularity}% - Similarity: {similarities[num - 1]}%")
        num = num + 1
        print("")

    print('-' * 400)
    print("")
