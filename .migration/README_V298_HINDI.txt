PODCAST GPT v2.98 — OFFLINE ADDITIVE PATCH
=========================================

GitHub access par HTTP 403 "Sorry. Your account was suspended" aaya;
isliye yeh version GitHub par push NAHI hua hai. Aapke local clone
(main par last known v2.97) mein new reviewer add karne ka patch hai.

Installation (NO model inference / NO downloads / NO GitHub push):
  1. Is ZIP ko unzip kijiye.
  2. APPLY_V298_TO_LOCAL_REPO.bat double-click kijiye.
  3. Apne existing podcast-gpt clone ka folder dijiye.
  4. Installer pehle `git apply --check` karta hai, phir patch apply.
     Files collision/tamper ho to bina overwrite kiye BLOCK karega.

Jab original Aarav, Meera, Kabir teeno ke ONE-ONE REAL verified
SadTalker source-bound talking-face MP4 clips saved hain, run:

  REVIEW_THREE_PRESENTER_PILOT.bat "D:\HindiStudio"

Windows browser mein offline 3 face clips dekhiye, command window mein
Enter pressed after review, then each speaker ke liye exact PASS/FAIL
likhiye; final requested acknowledgment bhi exact type kijiye.
Agar koi lip sync fail kare to FAIL likhiye. Record PRIVATE workspace
mein new JSON mein saved hoga. Kisi existing original file/video ko
overwrite nahi kiya jayega; AI model is review mein nahi chalega.

Read-only existing note inspection:
  REVIEW_THREE_PRESENTER_PILOT.bat "D:\HindiStudio" "" INSPECT

Important: PASS is a HUMAN OPINION for three short samples ONLY.
It is NOT 10-minute full video certification, identity/portrait rights
verification, automatic publication permission, or a new neural model.

Testing: 14/14 source-bound synthetic/offline unit tests PASS, using
fake media and injected mock original validators. Not tested with
real SadTalker or actual user's Windows CPU machine, and this offline
patch was NOT run in GitHub CI due account/API access blocker.

Complete details: docs/V298_RELEASE_NOTES.md (available inside .patch)