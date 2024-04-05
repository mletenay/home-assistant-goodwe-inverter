#!/bin/bash
#
# Script to test the integration in local home-assistant

DIR=$(dirname $0)

mkdir -p "$DIR/test_hass"

if [ ! -L "$DIR/test_hass/custom_components" ]; then
    # Create symlink from custom_components to hass subdir so it can be tested
    (cd "$DIR/test_hass" && ln -s "../custom_components" "custom_components")
fi

exec python3 -m homeassistant -c test_hass
