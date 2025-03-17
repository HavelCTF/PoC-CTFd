CTFd._internal.challenge.data = undefined;

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.renderer = null;

CTFd._internal.challenge.preRender = function () {};

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.render = null;

CTFd._internal.challenge.postRender = function () {
  const checkInterval = setInterval(() => {
    let dockerStart = document.getElementById("docker-start");
    if (dockerStart) {
      clearInterval(checkInterval);
      docker_status(CTFd._internal.challenge.data.id);
    }
  }, 100);
};

CTFd._internal.challenge.submit = function (preview) {
  var challenge_id = parseInt(CTFd.lib.$("#challenge-id").val());
  var submission = CTFd.lib.$("#challenge-input").val();

  var body = {
    challenge_id: challenge_id,
    submission: submission,
  };
  var params = {};
  if (preview) {
    params["preview"] = true;
  }

  return CTFd.api
    .post_challenge_attempt(params, body)
    .then(function (response) {
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
  const dockerStart = document.getElementById("docker-start");
  const dockerStatus = document.getElementById("docker-status");

  fetch("/havel-docker/api/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "CSRF-Token": init.csrfNonce,
    },
    body: JSON.stringify({ challenge_id: challenge_id }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      dockerStart.style.display = "none";
      dockerStatus.style.display = "block";
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function docker_stop(challenge_id) {
  const dockerStart = document.getElementById("docker-start");
  const dockerStatus = document.getElementById("docker-status");

  fetch("/havel-docker/api/stop", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "CSRF-Token": init.csrfNonce,
    },
    body: JSON.stringify({ challenge_id: challenge_id }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      dockerStart.style.display = "block";
      dockerStatus.style.display = "none";
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function docker_reset(challenge_id) {
  fetch("/havel-docker/api/reset", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "CSRF-Token": init.csrfNonce,
    },
    body: JSON.stringify({ challenge_id: challenge_id }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function docker_status(challenge_id) {
  const dockerSkeleton = document.getElementById("docker-skeleton");
  const dockerStart = document.getElementById("docker-start");
  const dockerStatus = document.getElementById("docker-status");

  fetch("/havel-docker/api/status", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "CSRF-Token": init.csrfNonce,
    },
    body: JSON.stringify({ challenge_id: challenge_id }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      dockerSkeleton.style.display = "none";
      if (data.status == "running") {
        dockerStart.style.display = "none";
        dockerStatus.style.display = "block";
      } else {
        dockerStart.style.display = "block";
        dockerStatus.style.display = "none";
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  const dockerHostname = document.getElementById("docker-hostname");

  fetch("/havel-docker/api/settings", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "CSRF-Token": init.csrfNonce,
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      dockerHostname.innerHTML = data.hostname;
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}
