# Implementation Plan

## [Overview]
This implementation will synchronize the cookie lifetime with the JWT token lifetime defined in the settings.

The current implementation sets JWT authentication cookies without an expiration, causing them to persist for the entire browser session. This plan will modify the login views to set the `max_age` of the cookies to match the `ACCESS_TOKEN_LIFETIME` and `REFRESH_TOKEN_LIFETIME` values from the `SIMPLE_JWT` settings.

## [Types]
No type system changes are required.

## [Files]
This implementation will modify one file.

-   **`userAuth/views.py`**: Update the `LoginView` and `LoginStudentAPIView` to include the `max_age` parameter when setting cookies.

## [Functions]
This implementation will modify two functions.

-   **`LoginView.post`** in `userAuth/views.py`:
    -   Add `max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()` to the `set_cookie` call for the access token.
    -   Add `max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()` to the `set_cookie` call for the refresh token.
-   **`LoginStudentAPIView.post`** in `userAuth/views.py`:
    -   Add `max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()` to the `set_cookie` call for the access token.
    -   Add `max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()` to the `set_cookie` call for the refresh token.

## [Classes]
No class modifications are required.

## [Dependencies]
No new dependencies are required.

## [Testing]
Testing will involve manual verification.

-   After logging in, use the browser's developer tools to inspect the cookies and confirm that the `access_token` and `refresh_token` cookies have an `Expires` or `Max-Age` attribute that matches the lifetimes set in `settings.py`.

## [Implementation Order]
The implementation will be done in a single step.

1.  Modify the `post` methods in the `LoginView` and `LoginStudentAPIView` classes in `userAuth/views.py` to set the `max_age` for the access and refresh token cookies.
