from flask import Flask, json, request, Response, jsonify
from flask_cors import CORS, cross_origin

from tinydb import TinyDB, Query, where
from cerberus import Validator
from urllib.parse import parse_qs

import jwt


app = Flask(__name__)
CORS(app, resources={r'*': {'origins': '*'}})

db = TinyDB('./db.json')

JWT_SECRET_KEY='secret'

Users = db.table('users')
Candidates = db.table('candidates')

# Schemas
UserGenerationDataSchema = {
  'email': {'type': 'string', 'required': True},
  'name': {'type': 'string', 'required': True},
  'password': {'type': 'string', 'required': True},
}

LoginDataSchema = {
  'email': {'type': 'string', 'required': True},
  'password': {'type': 'string', 'required': True},
}

UserGenerationDataSchemaValidator = Validator(UserGenerationDataSchema)
LoginDataSchemaValidator = Validator(LoginDataSchema)

Candidates.remove((lambda x: True))
Candidates.insert_multiple([
  {'name': '정시원', 'voteCount': 0},
  {'name': '고은', 'voteCount': 0},
  {'name': '유현우', 'voteCount': 0},
  {'name': '김진오', 'voteCount': 0},
  {'name': '문상빈', 'voteCount': 0},
  {'name': '문상진', 'voteCount': 0},
  {'name': '서유빈', 'voteCount': 0},
  {'name': '이재용', 'voteCount': 0},
  {'name': '장창훈', 'voteCount': 0},
  {'name': '황유나', 'voteCount': 0},
])

@app.route('/auth/signup', methods=['POST'])
def generateUser():
  userGenerationData = request.get_json(force=True)
  if not UserGenerationDataSchemaValidator(userGenerationData):
    return Response(response="올바른 요청 형식이 아닙니다", status=400)

  if Users.contains(Query()['email']==userGenerationData['email']):
    return Response(response="해당 유저에 대한 이메일이 이미 존재합니다", status=403)

  Users.insert(userGenerationData);
  return Response(response="성공적으로 생성되었습니다", status=201)

@app.route('/auth/login', methods=['POST'])
def verifyUser():
  loginData = request.get_json(force=True)
  if not LoginDataSchemaValidator(loginData):
    return Response(response="올바른 요청 형식이 아닙니다", status=400)

  if Users.contains((Query()['email'] == loginData['email']) and (Query()['password'] == loginData['password'])):
    return jwt.encode({'email': loginData['email']}, JWT_SECRET_KEY)
  else:
    return Response(response="이메일 혹은 비밀번호가 일치하지 않습니다", status=404)

@app.route('/auth/token', methods=['GET'])
def verifyToken():
  query = parse_qs(request.query_string)
  if not query.get(b'token'):
    return Response(response="token 쿼리가 존재하지 않습니다", status=400)
  token = query.get(b'token')[0]
  try:
    decoded = jwt.decode(token, JWT_SECRET_KEY)
    return Response(response="유효한 토큰입니다", status=200)
  except Exception as e:
    print(e)
    return Response(response="유효하지 않은 토큰입니다", status=401)
    pass

@app.route('/candidates', methods=['GET'])
def getAllCandidates():
  candidateList = Candidates.all()
  for candidate in candidateList:
    candidate['id'] = candidate.doc_id

  return Response(response=json.dumps(candidateList, ensure_ascii=False), mimetype="application/json")

@app.route('/vote')
def vote():
  query = parse_qs(request.query_string)
  if not query.get(b'id'):
    return Response(response="id 파라미터가 존재하지 않습니다", status=400)

  id = query.get(b'id')[0].decode('utf-8')
  targetCandidate = Candidates.get(doc_id=int(id))
  if not targetCandidate:
    return Response(response="해당 id를 가진 후보자가 존재하지 않습니다", status=404)

  Candidates.update({'voteCount': targetCandidate['voteCount'] + 1}, doc_ids=[int(id)])
  return Response(response=f"Successfully voted for number {id}({targetCandidate['name']})", status=200)

app.run(host="0.0.0.0", port=2020, debug=True)
