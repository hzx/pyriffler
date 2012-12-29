window.onload = ->
  # create loading structure
  wrapNode = document.createElement('div')
  wrapNode.id = 'loader-wrap'
  loaderNode = document.createElement('div')
  loaderNode.id = 'loader'
  text = document.createTextNode('{{ message }}')
  loaderNode.appendChild(text)
  wrapNode.appendChild(loaderNode)
  document.body.append(wrapNode)

  window.wender.browser.loadCss("{{ css }}")
  window.wender.browser.loadScript("{{ js }}", ->
    # remove loading structure
    wrapNode.parentNode.removeChild(wrapNode)
    window.{{app_name}}.main()
  )
