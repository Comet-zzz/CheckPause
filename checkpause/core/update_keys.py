"""Trust anchors for signed update manifests.

``UPDATE_PUBLIC_KEY`` is the Ed25519 public key embedded in every client. Its
private counterpart is kept outside the repositories (release machine only);
never put it in the repo, the app, or a build log. Rotating the key means
shipping a client that trusts the replacement.
"""

UPDATE_PUBLIC_KEY = "u/9Yopfrg+r5MFqGKsMiUFzXQDck+KDfjnmXOv4WIfc="
