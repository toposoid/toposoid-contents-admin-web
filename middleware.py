'''
  Copyright (C) 2025  Linked Ideal LLC.[https://linked-ideal.com/]
 
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation, version 3.
 
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.
 
  You should have received a copy of the GNU Affero General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
from model import StatusInfo
from fastapi.encoders import jsonable_encoder
from ToposoidCommon.model import StatusInfo, TransversalState
import ToposoidCommon as tc
LOG = tc.LogUtils(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        header_value = request.headers.get("X_TOPOSOID_TRANSVERSAL_STATE") or request.headers.get("X-TOPOSOID-TRANSVERSAL-STATE") or ""
        try:
            if header_value:
                transversalState = TransversalState.parse_raw(header_value.replace("'", "\""))
            else:
                raise Exception("An invalid TransversalState was detected.")                           
            response: Response = await call_next(request)
            if response.status_code != 200:
                LOG.error(f"StatusCode:{response.status_code}", transversalState)
                response = JSONResponse(content=jsonable_encoder(StatusInfo(status="ERROR", message=f"StatusCode:{response.status_code}")), status_code=response.status_code)
        except Exception as e:
            ambiguousTransversalState = TransversalState(userId="ambiguous", username="", roleId=0, csrfToken = "")
            LOG.error(e, ambiguousTransversalState)
            LOG.error(traceback.format_exc(), ambiguousTransversalState)
            response = JSONResponse(content=jsonable_encoder(StatusInfo(status="ERROR", message=traceback.format_exc())),status_code=500)

        return response
