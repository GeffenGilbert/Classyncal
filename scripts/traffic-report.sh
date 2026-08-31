#!/usr/bin/env bash
# Archive Caddy access logs to the host, then render GoAccess reports. Install
# on the box with:
#
#   chmod +x scripts/traffic-report.sh
#   (crontab -l 2>/dev/null; echo "30 3 * * * $PWD/scripts/traffic-report.sh >> $HOME/traffic/cron.log 2>&1") | crontab -
#
# Docker keeps container logs only until the container is recreated, and any
# Caddyfile change recreates caddy - so the log is not a durable record. This
# appends new lines to a monthly file under ~/traffic/archive first, then runs
# the report over the whole archive. GoAccess never sits in the request path;
# it only reads what Caddy already wrote.
#
# Two reports come out of it, because the raw one is dominated by noise: a
# public IP is scanned continuously by commodity vulnerability bots, and on the
# first run /wp-admin/install.php alone was 20% of all requests on a site that
# has never run WordPress. Counting those as visitors makes the number useless.
#
#   report.html      real traffic - scanners and probe paths removed
#   report-all.html  everything, unfiltered, for when a number looks wrong
#
# GoAccess's own --ignore-crawlers only knows self-declared crawlers, so it
# keeps zgrab and the rest; the filtering below is what actually removes them.

set -euo pipefail

DIR="${TRAFFIC_DIR:-$HOME/traffic}"
COMPOSE_DIR="${COMPOSE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ARCHIVE="$DIR/archive"
STAMP="$DIR/.last-run"

cd "$COMPOSE_DIR"
mkdir -p "$ARCHIVE"

SINCE=$(cat "$STAMP" 2>/dev/null || date -u -d "30 days ago" +%Y-%m-%dT%H:%M:%SZ)
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# GoAccess cannot parse Caddy's fractional epoch ts, so truncate to whole seconds.
docker compose logs --no-log-prefix --no-color --since "$SINCE" caddy 2>/dev/null \
  | grep "\"msg\":\"handled request\"" \
  | sed "s/\"ts\":\([0-9]*\)\.[0-9]*/\"ts\":\1/" \
  >> "$ARCHIVE/access-$(date -u +%Y-%m).json" || true
echo "$NOW" > "$STAMP"

# Paths nothing on this site serves: WordPress, PHP, dotfiles and the usual
# framework admin panels. A request for one is a probe by definition.
#
# Deliberately unanchored. Scanners walk a prefix list, so the same probe
# arrives as /wp-includes/..., /wordpress/wp-includes/..., /test/wp-includes/...
# and a dozen more; anchoring this at ^/ caught only the first and left several
# hundred nested variants counted as real traffic.
PROBE='wp-(admin|includes|content|login|json)|wlwmanifest|xmlrpc|phpmyadmin|autodiscover|boaform|hnap1|cgi-bin|/(vendor|actuator|solr|jenkins|hudson|telescope|_ignition|_profiler|owa)/|\.(php|env|git|aws|ssh|svn|hg|DS_Store)'

# Scanners, measurement services and command-line clients. "Mozilla/5.0 zgrab"
# looks like a browser until you read the tail, so match on the whole string.
SCANNER='zgrab|masscan|nmap|censys|expanse|palo ?alto|internet-measurement|leakix|netsystems|dataprovider|semrush|ahrefs|mj12|dotbot|bot|crawl|spider|scan|curl|wget|python-requests|go-http-client|libwww|okhttp|httpx|nuclei|scrapy'

LOGFMT='{"ts":"%x","request":{"client_ip":"%h","proto":"%H","method":"%m","uri":"%U","headers":{"User-Agent":["%u"],"Referer":["%R"]}},"size":"%b","status":"%s"}'

# GoAccess reads a stream on stdin; both reports use identical options so the
# only difference between them is what was fed in.
render() {  # render <output-file>, reading the log stream on stdin
  goaccess - \
    --log-format="$LOGFMT" --date-format=%s --time-format=%s \
    --ignore-crawlers --http-protocol=no --agent-list \
    -o "$1" 2>/dev/null
}

CLEAN=$(mktemp)
trap 'rm -f "$CLEAN"' EXIT

cat "$ARCHIVE"/access-*.json 2>/dev/null | jq -c --arg probe "$PROBE" --arg scanner "$SCANNER" '
  def ua: ((.request.headers."User-Agent" // [""])[0] // "");
  select((.request.uri // "") | test($probe; "i") | not)
  | select(ua | test($scanner; "i") | not)
  | select(ua != "" and ua != "-")
' > "$CLEAN"

cat "$ARCHIVE"/access-*.json 2>/dev/null | render "$DIR/report-all.html"
render "$DIR/report.html" < "$CLEAN"

ALL=$(cat "$ARCHIVE"/access-*.json 2>/dev/null | wc -l)
KEPT=$(wc -l < "$CLEAN")
echo "report: $DIR/report.html ($KEPT real of $ALL archived, $((ALL - KEPT)) filtered as bot/probe)"
