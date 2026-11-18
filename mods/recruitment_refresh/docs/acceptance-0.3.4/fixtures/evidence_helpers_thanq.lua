local function json(v)
 local kind=type(v)
 if kind=='nil' then return 'null' end
 if kind=='boolean' or kind=='number' then return tostring(v) end
 if kind=='string' then
  return '"'..v:gsub('[%z\1-\31\\"]',function(c)
   if c=='"' then return '\\"' elseif c=='\\' then return '\\\\' end
   return string.format('\\u%04x',string.byte(c))
  end)..'"'
 end
 assert(kind=='table')
 local parts={}
 if #v>0 then for _,item in ipairs(v) do parts[#parts+1]=json(item) end;return '['..table.concat(parts,',')..']' end
 for k,item in pairs(v) do parts[#parts+1]=json(tostring(k))..':'..json(item) end
 return '{'..table.concat(parts,',')..'}'
end
local function save(name,value)
 local f=assert(io.open('D:/workspace/.codex-wh3-runtime/dlc-round2-20261118/evidence-thanq-034/'..name..'.json','w'));f:write(json(value));f:close()
end

xatw3_test.save=save
