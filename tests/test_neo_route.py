from datetime import datetime as real_datetime
from unittest.mock import patch


def test_neo_uses_requested_timezone_not_server_time(client):
    # REGRESSION: `start = datetime.now()` used the server's local clock
    # (UTC in production) to compute the 7-day NEO window, ignoring the `tz`
    # query param entirely -- even though tz_name is resolved on the line
    # right above it and threaded through to get_neo_list for date-string
    # formatting. Near local midnight this shifts the window's start date
    # by a day relative to the requested timezone's "today". Same bug class
    # already fixed for /hours, /tonight, and /whatsup-next.
    with patch("app.routes.neo.get_neo_list", return_value={"near_earth_objects": {}}), \
         patch("app.routes.neo.datetime") as mock_datetime:
        mock_datetime.now.side_effect = lambda *a, **kw: real_datetime.now(*a, **kw)

        resp = client.get("/v1/space/neo?tz=America/Los_Angeles")

    assert resp.status_code == 200
    mock_now = mock_datetime.now
    assert mock_now.called
    args, kwargs = mock_now.call_args
    tz_arg = args[0] if args else kwargs.get("tz")
    assert tz_arg is not None
    assert str(tz_arg) == "America/Los_Angeles"
