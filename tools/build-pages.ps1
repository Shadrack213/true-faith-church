# Generates every inner page linked from the main navigation.
# The header and footer are copied verbatim from index.html (between the
# HEADER/FOOTER START/END markers), so the navigation stays identical site-wide.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File tools\build-pages.ps1

$root = Split-Path -Parent $PSScriptRoot
$utf8 = New-Object System.Text.UTF8Encoding($false)
$index = [IO.File]::ReadAllText((Join-Path $root 'index.html'), $utf8)

function Get-Block($text, $name) {
  $start = "<!-- $name START -->"
  $end = "<!-- $name END -->"
  $i = $text.IndexOf($start)
  $j = $text.IndexOf($end)
  if ($i -lt 0 -or $j -lt 0) { throw "Markers for $name not found in index.html" }
  return $text.Substring($i, $j + $end.Length - $i)
}
$header = Get-Block $index 'HEADER'
$footer = Get-Block $index 'FOOTER'

$img = @{
  church  = 'https://images.pixieset.com/572383421/8407ee5c61062970eec4ba9c55f69684-xxlarge.JPG'
  worship = 'https://images.pixieset.com/572383421/cbff73764912c15834d5d812b1620027-xxlarge.JPG'
  bible   = 'https://images.pixieset.com/572383421/7bb6dff66d9fb1fb0172fdc77132800a-xxlarge.JPG'
  hands   = 'https://images.pixieset.com/572383421/2f5a70deb0c48838b80598ba0c879abc-xxlarge.JPG'
  crowd   = 'https://images.pixieset.com/572383421/b411688933ede73d7512a9b1892155e0-xxlarge.JPG'
  praise  = 'https://images.pixieset.com/572383421/691be82d8cf8a01c112a69c5dd39992d-xxlarge.JPG'
}

# Sibling groups (mirrors the dropdowns exactly)
$groups = @{
  'Events' = @(
    @('events-national.html', 'National Events'),
    @('events-regional.html', 'Regional Events'),
    @('events-district.html', 'District Events'))
  'Find a Church' = @(
    @('church-headquarters.html', 'Headquarters'),
    @('church-ghana.html', 'Ghana'),
    @('church-cote-divoire.html', 'C&ocirc;te d&rsquo;Ivoire'),
    @('church-togo.html', 'Togo'),
    @('church-usa.html', 'USA'),
    @('church-uk.html', 'UK'),
    @('church-canada.html', 'Canada'),
    @('church-dubai.html', 'Dubai'))
  'Leadership' = @(
    @('leadership-headquarters.html', 'Headquarters'),
    @('leadership-districts.html', 'Districts'),
    @('leadership-zones.html', 'Zones'))
  'Ministries' = @(
    @('ministry-women-commission.html', 'Women Commission'),
    @('ministry-church-administration.html', 'Church Administration'),
    @('ministry-youth.html', 'Youth Ministry'),
    @('ministry-evangelism.html', 'Evangelism Ministry'),
    @('ministry-children.html', "Children's Ministry"),
    @('ministry-prophetic.html', 'Prophetic Ministry'),
    @('ministry-soul.html', 'Soul Ministry'))
}

# Page content (official church text) lives in tools/content/pages.json, read as
# UTF-8 so accented names and dashes survive. Each entry:
#   file, title, group (or null), bg, sub, h2/heading (optional), intro,
#   cards: [[icon, title, html], ...], extra (optional HTML fragment in tools/content)
$contentDir = Join-Path $PSScriptRoot 'content'
$pages = [IO.File]::ReadAllText((Join-Path $contentDir 'pages.json'), $utf8) | ConvertFrom-Json
$byFile = @{}
foreach ($x in $pages) { $byFile[$x.file] = $x }

foreach ($pg in $pages) {
  $g = $pg.group
  $heading = if ($pg.heading) { $pg.heading }
             elseif ($g -eq 'Find a Church') { "True Faith Church International &mdash; $($pg.title)" }
             elseif ($g -eq 'Leadership') { "$($pg.title) Leadership" }
             else { $pg.title }
  $crumbs = '<li><a href="index.html">Home</a></li>'
  if ($g -eq 'Ministries') { $crumbs += '<li><a href="ministries.html">Ministries</a></li>' }
  elseif ($g) { $crumbs += "<li>$g</li>" }
  $crumbs += "<li aria-current=`"page`">$($pg.title)</li>"

  $cardHtml = ($pg.cards | ForEach-Object {
    "        <div class=`"info-card reveal`"><div class=`"icon-box`"><i class=`"$($_[0])`"></i></div><h3>$($_[1])</h3><p>$($_[2])</p></div>"
  }) -join "`n"

  # Optional "showcase": a centre image with the page's cards floating around it
  # as numbered glass cards. Otherwise the cards render as the normal grid.
  $cardsBlock = "      <div class=`"info-grid`">`n$cardHtml`n      </div>`n"
  if ($pg.showcase) {
    $total = @($pg.cards).Count
    $n = 0
    $slides = (@($pg.cards) | ForEach-Object {
      $n++
      $active = if ($n -eq 1) { ' is-active' } else { '' }
      "            <div class=`"hq-slide$active`" role=`"group`" aria-roledescription=`"slide`" aria-label=`"$n of $total`"><h3>$($_[1])</h3><p>$($_[2])</p></div>"
    }) -join "`n"
    $cardsBlock = @"
      <div class="hq-showcase">
        <div class="hq-intro reveal">
          <h3 class="hq-headline">Join us for<br>worship.</h3>
          <a class="hq-discover" href="#branches">View locations <i class="fa-solid fa-arrow-down" aria-hidden="true"></i></a>
        </div>
        <div class="hq-slider reveal" data-hq-slider aria-roledescription="carousel" aria-label="Church details">
          <div class="hq-slides">
$slides
          </div>
          <div class="hq-slider-foot">
            <a href="contact.html" class="hq-more">Contact Us</a>
            <span class="hq-count" aria-live="polite"><b data-hq-current>01</b>/0$total</span>
          </div>
          <div class="hq-arrows">
            <button type="button" data-hq-prev aria-label="Previous detail"><i class="fa-solid fa-arrow-left"></i></button>
            <button type="button" data-hq-next aria-label="Next detail"><i class="fa-solid fa-arrow-right"></i></button>
          </div>
          <span class="hq-progress" aria-hidden="true"><i data-hq-progress></i></span>
        </div>
        <figure class="hq-building reveal"><img src="$($pg.showcase[0])" alt="$($pg.showcase[1])" loading="lazy"></figure>
      </div>

"@
  }

  # Optional leadership team: [name, role, photo-url (optional)].
  # Without a photo the card shows a neutral silhouette.
  $teamHtml = ''
  if ($pg.team) {
    $people = (@($pg.team) | ForEach-Object {
      $photo = if ($_.Count -gt 2 -and $_[2]) { "<img src=`"$($_[2])`" alt=`"$($_[0]), $($_[1])`" loading=`"lazy`">" } else { "<i class=`"fa-solid fa-user`" aria-hidden=`"true`"></i>" }
      "        <div class=`"team-card reveal`"><figure class=`"team-photo`">$photo</figure><div class=`"team-name`"><h3>$($_[0])</h3><p>$($_[1])</p></div></div>"
    }) -join "`n"
    $teamHtml = "      <div class=`"team-grid`">`n$people`n      </div>`n"
  }

  # Optional branch lists (Find a Church). Cities are location references only,
  # so every card says the address is still to be confirmed.
  $branchHtml = ''
  foreach ($bg in @($pg.branchGroups)) {
    if (-not $bg) { continue }
    $blockId = if ($branchHtml) { '' } else { ' id="branches"' }
    $bcards = (@($bg.branches) | ForEach-Object {
      "        <div class=`"info-card reveal`"><div class=`"icon-box`"><i class=`"fa-solid fa-location-dot`"></i></div><h3>$($_[0])</h3><p>$($_[1])</p><p class=`"branch-note`">Address to be confirmed</p></div>"
    }) -join "`n"
    $branchHtml += @"
      <div class="branch-block"$blockId>
        <div class="section-title section-title-center">
          <span class="section-sub-title">$($bg.sub)</span>
          <h2>$($bg.title)</h2>
          <p>$($bg.intro)</p>
        </div>
        <div class="info-grid">
$bcards
        </div>
      </div>

"@
  }
  if ($branchHtml) {
    $branchHtml += "      <p class=`"branch-disclaimer`">Listed cities are location references. Exact branch addresses are to be confirmed &mdash; please contact the headquarters for the branch nearest you.</p>`n"
  }

  $extra = ''
  if ($pg.extra) { $extra = [IO.File]::ReadAllText((Join-Path $contentDir $pg.extra), $utf8) }

  $siblings = ''
  if ($g) {
    $links = ($groups[$g] | ForEach-Object {
      $cls = if ($_[0] -eq $pg.file) { ' class="current" aria-current="page"' } else { '' }
      "<a href=`"$($_[0])`"$cls>$($_[1])</a>"
    }) -join ''
    $siblings = "      <div class=`"sibling-nav`" aria-label=`"$g pages`">$links</div>"
  }

  # Tokens a shared `extra` fragment can use (e.g. one Events layout for all three pages)
  $extra = $extra.Replace('{{TITLE}}', $pg.title).Replace('{{BG}}', $img[$pg.bg]).Replace('{{CRUMBS}}', $crumbs).Replace('{{SIBLINGS}}', $siblings)

  # "ownHeader": true pages draw their own hero inside `extra`
  $pageHeader = ''
  if (-not $pg.ownHeader) {
    $pageHeader = @"
  <section class="page-header dark-section">
    <div class="page-bg" style="background-image:url('$($img[$pg.bg])')"></div>
    <div class="container">
      <h1>$heading</h1>
      <ol class="breadcrumb">$crumbs</ol>
    </div>
  </section>

"@
  }

  # "custom": true pages (e.g. About Us) supply their whole body in `extra`
  # and skip the generic intro + card block.
  $contentSection = ''
  if (-not $pg.custom) {
    $contentSection = @"
  <section class="page-content">
    <div class="container">
      <div class="section-title section-title-center">
        <span class="section-sub-title">$($pg.sub)</span>
        <h2>$(if ($pg.h2) { $pg.h2 } else { $pg.title })</h2>
        <p>$($pg.intro)</p>
      </div>
$teamHtml$cardsBlock$branchHtml$siblings
    </div>
  </section>
"@
  }

  # "layout": "ministry" -> article (intro, sections, two photos) + sidebar of the other ministries
  if ($pg.layout -eq 'ministry') {
    $sections = @($pg.cards) | ForEach-Object { "          <h3>$($_[1])</h3>`n          <p>$($_[2])</p>" }
    $photosHtml = (@($pg.photos) | ForEach-Object { "<figure class=`"img-frame`"><img src=`"$($_[0])`" alt=`"$($_[1])`" loading=`"lazy`"></figure>" }) -join ''
    $restHtml = ($sections | Select-Object -Skip 1) -join "`n"
    $others = ($groups[$g] | Where-Object { $_[0] -ne $pg.file } | ForEach-Object {
      $o = $byFile[$_[0]]
      "            <li><a href=`"$($_[0])`"><img src=`"$($o.thumb)`" alt=`"`" loading=`"lazy`"><span><small>TFCI Ministries</small><strong>$($_[1])</strong></span></a></li>"
    }) -join "`n"
    $contentSection = @"
  <section class="page-content">
    <div class="container">
      <div class="ministry-detail">
        <article class="ministry-article">
          <p class="ministry-lead">$($pg.intro)</p>
$($sections[0])
          <div class="ministry-photos">$photosHtml</div>
$restHtml
        </article>
        <aside class="ministry-sidebar" aria-label="Other ministries">
          <div class="sidebar-box">
            <h3>Other Ministries</h3>
            <ul class="sidebar-posts">
$others
            </ul>
            <a href="ministries.html" class="readmore-btn">All Ministries</a>
          </div>
        </aside>
      </div>
    </div>
  </section>
"@
  }

  # "grid": "<group>" -> overview of that group's pages as photo tiles
  if ($pg.grid) {
    $tiles = ($groups[$pg.grid] | ForEach-Object {
      $o = $byFile[$_[0]]
      "        <a class=`"ministry-tile reveal`" href=`"$($_[0])`"><img src=`"$($o.thumb)`" alt=`"`" loading=`"lazy`"><span class=`"ministry-tile-body`"><small>TFCI Ministries</small><strong>$($_[1])</strong><i class=`"fa-solid fa-arrow-right`" aria-hidden=`"true`"></i></span></a>"
    }) -join "`n"
    $contentSection = @"
  <section class="page-content">
    <div class="container">
      <div class="section-title section-title-center">
        <span class="section-sub-title">$($pg.sub)</span>
        <h2>Our Ministries</h2>
        <p>$($pg.intro)</p>
      </div>
      <div class="ministry-tiles">
$tiles
      </div>
    </div>
  </section>
"@
  }

  $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>$heading &mdash; True Faith Church International</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Phudu:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>

$header

<main>
$pageHeader$contentSection$extra
</main>

$footer

<script src="assets/js/main.js"></script>
</body>
</html>
"@
  [IO.File]::WriteAllText((Join-Path $root $pg.file), $html, $utf8)
  Write-Output "wrote $($pg.file)"
}
