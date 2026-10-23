/* ==========================================================================
   SEMI-GUARD: Firebase Authentication & Firestore Integration Module
   Project: iceu-songpa03
   Features: Email/Password Sign-Up, Sign-In, Role Assignment, Auth State Observer
   ========================================================================== */

const firebaseConfig = {
  apiKey: "AIzaSyDyjdSJIzfBFYIZeoLV_L4ICWNBUeDT6cU",
  authDomain: "iceu-songpa03.firebaseapp.com",
  databaseURL: "https://iceu-songpa03-default-rtdb.firebaseio.com",
  projectId: "iceu-songpa03",
  storageBucket: "iceu-songpa03.firebasestorage.app",
  messagingSenderId: "94943462326",
  appId: "1:94943462326:web:e9b83fd642131479243717",
  measurementId: "G-D1595VRDL6"
};

let firebaseApp = null;
let firebaseAuth = null;
let firestoreDb = null;

try {
  if (typeof firebase !== 'undefined') {
    firebaseApp = firebase.initializeApp(firebaseConfig);
    firebaseAuth = firebase.auth();
    firestoreDb = firebase.firestore();
    console.log("🔥 Firebase Auth & Firestore successfully connected to iceu-songpa03!");
  } else {
    console.warn("Firebase SDK script not loaded yet.");
  }
} catch (err) {
  console.warn("Firebase Init note:", err);
}

// User Profile Cache
function getUserRole(uid, fallbackRole = 'engineer') {
  const cached = localStorage.getItem(`semiguard_role_${uid}`);
  return cached || fallbackRole;
}

function getUserName(uid, fallbackName = '') {
  const cached = localStorage.getItem(`semiguard_name_${uid}`);
  return cached || fallbackName;
}

function getUserStatus(uid, fallbackStatus = 'pending') {
  const cached = localStorage.getItem(`semiguard_status_${uid}`);
  return cached || fallbackStatus;
}

// Multi-Channel Sync to Firestore named database 'project' (Collection: users) & Local DB
async function syncUserToProjectFirestore(uid, role, name, email, status = 'pending', isApproved = false) {
  const finalName = name || (email ? email.split('@')[0] : '사용자');
  const targetRole = role || 'engineer';
  
  // Pre-approve initial admin emails
  if (email && (email.toLowerCase() === 'admin@semiguard.fab' || email.toLowerCase().startsWith('admin@'))) {
    status = 'approved';
    isApproved = true;
  }
  
  console.log(`📡 [User Sync] Syncing user ${uid} (${finalName}) [Status: ${status}, Approved: ${isApproved}]...`);

  // 1. Server-Side Sync via Cloud Run API (Local SQLite + Cloud Firestore)
  try {
    const res = await fetch('/api/sync-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uid: uid,
        email: email || '',
        name: finalName,
        displayName: finalName,
        role: targetRole,
        status: status,
        isApproved: isApproved
      })
    });
    const data = await res.json();
    console.log("✅ [Cloud Run Sync] Response:", data);
  } catch (e) {
    console.warn("[Cloud Run Sync] notice:", e);
  }

  // 2. Client-Side Direct REST Sync with Firebase User Token (if logged in)
  try {
    if (firebaseAuth && firebaseAuth.currentUser) {
      const idToken = await firebaseAuth.currentUser.getIdToken();
      const url = `https://firestore.googleapis.com/v1/projects/iceu-songpa03/databases/project/documents/users/${uid}`;
      const payload = {
        fields: {
          email: { stringValue: email || '' },
          name: { stringValue: finalName },
          displayName: { stringValue: finalName },
          role: { stringValue: targetRole },
          status: { stringValue: status },
          isApproved: { booleanValue: isApproved },
          updatedAt: { timestampValue: new Date().toISOString() }
        }
      };
      fetch(url, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      }).then(r => r.json()).catch(err => console.warn("[Client REST Sync] notice:", err));
    }
  } catch (e) {
    console.warn("[Client REST Sync] error:", e);
  }

  // 3. Fallback write to default compat Firestore if initialized
  if (firestoreDb && uid) {
    firestoreDb.collection('users').doc(uid).set({
      role: targetRole,
      displayName: finalName,
      name: finalName,
      email: email || '',
      status: status,
      isApproved: isApproved,
      updatedAt: firebase.firestore.FieldValue.serverTimestamp()
    }, { merge: true }).catch(err => console.log('Firestore default instance note:', err));
  }
}

function setUserProfile(uid, role, name, email, status = 'pending', isApproved = false) {
  if (role) localStorage.setItem(`semiguard_role_${uid}`, role);
  if (name) localStorage.setItem(`semiguard_name_${uid}`, name);
  if (status) localStorage.setItem(`semiguard_status_${uid}`, status);
  localStorage.setItem(`semiguard_approved_${uid}`, isApproved ? 'true' : 'false');
  if (email && name) localStorage.setItem(`semiguard_name_${email}`, name);
  if (email && role) localStorage.setItem(`semiguard_role_${email}`, role);
  
  syncUserToProjectFirestore(uid, role, name, email, status, isApproved);
}

// Check approval status from server or cache
async function checkUserApprovalStatus(uid, email) {
  // Pre-approve system admin emails
  if (email && (email.toLowerCase() === 'admin@semiguard.fab' || email.toLowerCase().startsWith('admin@'))) {
    return { status: 'approved', isApproved: true };
  }
  
  // 1. Try server API
  try {
    const res = await fetch(`/api/user-status/${uid}`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.found) {
        return { status: data.status, isApproved: data.isApproved, role: data.role, name: data.name };
      }
    }
  } catch(e) {}

  // 2. Try Firestore REST directly
  try {
    if (firebaseAuth && firebaseAuth.currentUser) {
      const idToken = await firebaseAuth.currentUser.getIdToken();
      const res = await fetch(`https://firestore.googleapis.com/v1/projects/iceu-songpa03/databases/project/documents/users/${uid}`, {
        headers: { 'Authorization': `Bearer ${idToken}` }
      });
      if (res.ok) {
        const doc = await res.json();
        if (doc && doc.fields) {
          const status = doc.fields.status?.stringValue || 'pending';
          const isApproved = doc.fields.isApproved?.booleanValue ?? (status === 'approved');
          return { status, isApproved };
        }
      }
    }
  } catch (e) {}

  // 3. LocalStorage fallback
  const cachedStatus = localStorage.getItem(`semiguard_status_${uid}`) || 'pending';
  const cachedApproved = localStorage.getItem(`semiguard_approved_${uid}`) === 'true';
  return { status: cachedStatus, isApproved: cachedApproved };
}

// Sign Up with Firebase (Initial status: PENDING approval by Admin)
async function handleFirebaseSignUp(email, password, role, displayName) {
  if (!firebaseAuth) {
    throw new Error("Firebase SDK가 로드되지 않았습니다.");
  }
  const userCredential = await firebaseAuth.createUserWithEmailAndPassword(email, password);
  const user = userCredential.user;
  const finalName = displayName || email.split('@')[0];
  
  if (finalName && user.updateProfile) {
    try {
      await user.updateProfile({ displayName: finalName });
    } catch(e) {
      console.warn("User updateProfile notice:", e);
    }
  }

  // Admin emails are pre-approved; general engineers require admin approval
  const isAdminEmail = email.toLowerCase() === 'admin@semiguard.fab' || email.toLowerCase().startsWith('admin@');
  const initialStatus = isAdminEmail ? 'approved' : 'pending';
  const initialApproved = isAdminEmail;
  
  setUserProfile(user.uid, role, finalName, email, initialStatus, initialApproved);
  await syncUserToProjectFirestore(user.uid, role, finalName, email, initialStatus, initialApproved);

  // If pending, immediately sign out to prevent unauthorized entry
  if (!initialApproved) {
    await firebaseAuth.signOut();
  }

  return { user, role, displayName: finalName, status: initialStatus, isApproved: initialApproved };
}

// Sign In with Firebase (Enforces ADMIN APPROVAL)
async function handleFirebaseSignIn(email, password, roleHint) {
  if (!firebaseAuth) {
    throw new Error("Firebase SDK가 로드되지 않았습니다.");
  }
  const userCredential = await firebaseAuth.signInWithEmailAndPassword(email, password);
  const user = userCredential.user;

  // Check Admin Approval Status
  const approval = await checkUserApprovalStatus(user.uid, user.email);
  if (approval.status === 'pending' || !approval.isApproved) {
    await firebaseAuth.signOut();
    const err = new Error("사내 공정 관리자(Admin)의 가입 승인 대기 중인 계정입니다. 관리자 승인 완료 후 이용하실 수 있습니다.");
    err.code = 'auth/approval-pending';
    throw err;
  }
  if (approval.status === 'rejected') {
    await firebaseAuth.signOut();
    const err = new Error("회원가입 신청이 반려(거절)된 계정입니다. 공정 관리자에게 문의하세요.");
    err.code = 'auth/approval-rejected';
    throw err;
  }

  let role = approval.role || getUserRole(user.uid, roleHint || 'engineer');
  let displayName = user.displayName || getUserName(user.uid) || approval.name || email.split('@')[0];
  
  setUserProfile(user.uid, role, displayName, email, 'approved', true);
  return { user, role, displayName, status: 'approved', isApproved: true };
}

// Sign Out with Firebase
async function handleFirebaseSignOut() {
  if (firebaseAuth) {
    await firebaseAuth.signOut();
  }
}

// Register Auth State Observer (Validates Approval on session restore)
function setupFirebaseAuthObserver(onUserChange) {
  if (!firebaseAuth) return;
  
  firebaseAuth.onAuthStateChanged(async (user) => {
    if (user) {
      if (user.email) localStorage.setItem('semiguard_current_email', user.email);
      
      // Verify approval status before auto-login
      const approval = await checkUserApprovalStatus(user.uid, user.email);
      if (approval.status === 'pending' || !approval.isApproved) {
        console.warn("⚠️ User session blocked: Pending Admin approval for", user.email);
        await firebaseAuth.signOut();
        onUserChange({
          isLoggedIn: false,
          isPending: true,
          uid: user.uid,
          email: user.email,
          role: 'engineer'
        });
        return;
      }
      if (approval.status === 'rejected') {
        await firebaseAuth.signOut();
        onUserChange({
          isLoggedIn: false,
          isRejected: true,
          uid: user.uid,
          email: user.email,
          role: 'engineer'
        });
        return;
      }

      let role = approval.role || getUserRole(user.uid, 'engineer');
      let displayName = user.displayName || getUserName(user.uid) || user.email.split('@')[0];
      
      onUserChange({
        isLoggedIn: true,
        uid: user.uid,
        email: user.email,
        name: displayName,
        role: role,
        status: 'approved',
        isApproved: true
      });
    } else {
      onUserChange({
        isLoggedIn: false,
        uid: null,
        email: null,
        role: 'engineer'
      });
    }
  });
}

// Admin APIs for Approval Management
async function fetchAdminUserList() {
  const res = await fetch('/api/admin/users');
  if (!res.ok) throw new Error("사용자 목록을 불러올 수 없습니다.");
  return await res.json();
}

async function approveUserAccount(uid, approve = true, adminEmail = 'admin@semiguard.fab') {
  const res = await fetch('/api/admin/approve-user', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      uid: uid,
      status: approve ? 'approved' : 'rejected',
      adminEmail: adminEmail
    })
  });
  if (!res.ok) throw new Error("승인 처리에 실패했습니다.");
  return await res.json();
}

