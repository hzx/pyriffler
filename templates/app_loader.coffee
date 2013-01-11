
window.onload = ->
  w = window.wender
  E = w.DomElement
  T = w.DomText

  # create loading structure
  loader = new E("div", {"id": "loader-wrap"}, [
    new E("div", {"id": "loader"}, [
      new T("{{ message }}", null, null)
    ], null, null)
  ], null, null)

  w.init()

  w.browser.appendElement(loader)

  w.browser.loadCss("{{ css }}")
  w.browser.loadScript "{{ js }}", ->
    # run application
    window.{{app_name}}.main ->
      loader.addClass("hidden-smooth")
