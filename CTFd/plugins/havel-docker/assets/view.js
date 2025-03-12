CTFd._internal.challenge.data = undefined;

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.renderer = null;

CTFd._internal.challenge.preRender = function() {};

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.render = null;

CTFd._internal.challenge.postRender = function() {};

CTFd._internal.challenge.submit = function(preview) {
  var challenge_id = parseInt(CTFd.lib.$("#challenge-id").val());
  var submission = CTFd.lib.$("#challenge-input").val();

  var body = {
    challenge_id: challenge_id,
    submission: submission
  };
  var params = {};
  if (preview) {
    params["preview"] = true;
  }

  return CTFd.api.post_challenge_attempt(params, body).then(function(response) {
    if (response.status === 429) {
      // User was ratelimited but process response
      return response;
    }
    if (response.status === 403) {
      // User is not logged in or CTF is paused.
      return response;
    }
    return response;
  });
};

function docker_start(challenge_id) {
  console.log("Starting docker for challenge " + challenge_id);

  const dockerStart = document.getElementById("docker-start");
  const dockerStatus = document.getElementById("docker-status");

  dockerStart.style.display = "none";
  dockerStatus.style.display = "block";
}

function docker_stop(challenge_id) {
  console.log("Stopping docker for challenge " + challenge_id);

  const dockerStart = document.getElementById("docker-start");
  const dockerStatus = document.getElementById("docker-status");

  dockerStart.style.display = "block";
  dockerStatus.style.display = "none";
}

function docker_reset(challenge_id) {
  console.log("Resetting docker for challenge " + challenge_id);
}

function docker_renew(challenge_id) {
  console.log("Renewing docker for challenge " + challenge_id);
}
