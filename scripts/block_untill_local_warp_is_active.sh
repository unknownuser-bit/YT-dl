tries=$1

if [ -z $tries ]; then
    tries=30
fi

echo "waiting for warp $tries times"

for i in {1..$tries}; do
    sleep 1
    RESULT=$(curl -s --max-time 10 --socks5-hostname 127.0.0.1:1080 https://cloudflare.com/cdn-cgi/trace 2>/dev/null || echo "failed")
    echo "$RESULT"
    if echo "$RESULT" | grep -qE "warp=(on|plus)"; then
        echo "✅ WARP is active!"
        echo "$RESULT"
        exit 0
    fi
done

echo "warp was not activated"
exit 1