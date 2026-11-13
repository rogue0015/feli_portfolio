/* Blog index: filter posts by tag.
   Every post is present in the markup (in #post-list plus an #all-posts template
   holding the full set), so filtering works across paginated pages and all
   articles stay crawlable. With JavaScript off the paginated list is used. */
(function () {
  var select = document.getElementById('tag-filter');
  var list = document.getElementById('post-list');
  if (!select || !list) return;
  var template = document.getElementById('all-posts');
  var note = document.getElementById('filter-note');
  var pager = document.querySelector('.index-pager');
  var original = list.innerHTML;

  function matches(li, tag) {
    var tags = ' ' + (li.getAttribute('data-tags') || '') + ' ';
    return tags.indexOf(' ' + tag + ' ') !== -1;
  }

  function apply(tag) {
    if (!tag) {
      list.innerHTML = original;
      if (pager) pager.hidden = false;
      if (note) note.hidden = true;
      return;
    }
    var source = template ? template.content.querySelectorAll('li') : list.querySelectorAll('li');
    var html = '', n = 0;
    for (var i = 0; i < source.length; i++) {
      if (matches(source[i], tag)) { html += source[i].outerHTML; n++; }
    }
    list.innerHTML = html;
    if (pager) pager.hidden = true;
    if (note) {
      note.hidden = false;
      note.textContent = n + (n === 1 ? ' post tagged ' : ' posts tagged ') + '\u201C' + tag + '\u201D';
    }
  }

  select.addEventListener('change', function () { apply(select.value); });
})();
