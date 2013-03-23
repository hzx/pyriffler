
window.onload = ->
  w = window.wender
  E = w.DomElement
  T = w.DomText

  # create loading structure
  loaderView = new E("div", {"id": "loader_wrap"}, [
    new E("div", {"id": "loader"}, [
      new T("{{ message }}", null, null)
    ], null, null)
  ], null, null)

  w.init()

  w.browser.appendElement(loaderView)

  loader = new w.Loader()
  loader.load([
    ["{{ css }}", 'css'],
    ["{{ js }}", 'js']
  ], () ->
    window.{{app_name}}.main ->
      loaderView.addClass("hidden_smooth")
      window.setTimeout ->
        loaderView.addClass("hidden")
      , 1000
  , (status) ->
    alert(status)
  )

  # w.browser.loadCss("{{ css }}")
  # w.browser.loadScript "{{ js }}", ->
  #   # run application
  #   window.{{app_name}}.main ->
  #     loaderView.addClass("hidden_smooth")
  #     window.setTimeout ->
  #       loaderView.addClass("hidden")
  #     , 1000
