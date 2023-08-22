swagger_create_token = {
    "401": {
        "description": "Unauthorized(RefreshToken)",
        "content": {
            "application/json": {
                "schema": {
                    "title": "Not authorized RefreshToken",
                    "description": "invalid refresh token",
                    "example": {
                        "description": "Invalid refresh token"
                    }
                },
            }
        },
    },
}

swagger_register = {
    "400": {
        "description": "Bad request",
        "content": {
            "application/json": {
                "schema": {
                    "title": "Email is busy",
                    "description": "An account with this email "
                                   "has already been registered",
                    "example": {
                        "description": "An account with this email "
                                       "has already been registered"
                    }
                },
            }
        },
    },
}

swagger_login = {
    "404": {
        "description": "Bad request",
        "content": {
            "application/json": {
                "schema": {
                    "title": "Invalid username or password",
                    "description": "Invalid username or password",
                    "example": {
                        "description": "Invalid username or password"
                    }
                },
            }
        },
    },
}

swagger_change_password = {
    "200": {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "schema": {
                    "title": "Сhanging the password",
                    "description": "Password changed successfully",
                    "example": "Password changed successfully"
                },
            }
        },
    },
    "400": {
        "description": "Bad request",
        "content": {
            "application/json": {
                "schema": {
                    "oneOf": [
                        {
                            "title": "Invalid new password or "
                                     "repeated password",
                            "description": "The new password does not "
                                           "match the repeated password",
                            "example": {
                                "description": "The new password does not "
                                               "match the repeated password"
                            },
                        },
                        {
                            "title": "Invalid new password",
                            "description": "The new password must not "
                                           "match the old password",
                            "example": {
                                "description": "The new password must not"
                                               " match the old password"
                            },
                        },
                        {
                            "title": "Invalid old password",
                            "description": "The current password was "
                                           "entered incorrectly",
                            "example": {
                                "description": "The current password was "
                                               "entered incorrectly"
                            },
                        },
                    ]
                },
            }
        },
    },
}
