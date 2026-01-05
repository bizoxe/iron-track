-- signup.lua
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"

local counter = 0

request = function()
   counter = counter + 1
   -- Комбинируем время и счетчик для 100% уникальности
   local email = "fix_" .. os.clock() .. "_" .. counter .. "@test.com"
   local payload = string.format(
      '{"name":"Tester", "email":"%s", "password":"Strong_Password123", "confirm_password":"Strong_Password123"}',
      email
   )
   return wrk.format(nil, nil, nil, payload)
end

