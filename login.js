var state = null;

FB.login(function(response) {
  if (response.status === 'connected') {
    // Logged into your app and Facebook.
    state = response.authResponse;
  } else if (response.status === 'not_authorized') {
    // The person is logged into Facebook, but not your app.
  } else {
    // The person is not logged into Facebook, so we're not sure if
    // they are logged into this app or not.
  }
});
