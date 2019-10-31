from selenium import webdriver
driver = webdriver.PhantomJS()
driver.get("https://www.mangaupdates.com/series.html?id=110706")

print(driver.page_source)