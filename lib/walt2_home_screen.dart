// -- lib/walt2_home_screen.dart
import 'package:flutter/material.dart';
import 'api_service.dart';
import 'dart:async';
import 'dart:io';
import 'package:path_provider/path_provider.dart';

class Walt2HomeScreen extends StatefulWidget {
  final String initialMessage;
  final ApiService apiService;
  // final bool loadStoryOnInit; // Removed loadStoryOnInit

  const Walt2HomeScreen({
    super.key,
    required this.initialMessage,
    required this.apiService,
    // this.loadStoryOnInit = false, // Removed loadStoryOnInit
  });

  @override
  _Walt2HomeScreenState createState() => _Walt2HomeScreenState();
}

class _Walt2HomeScreenState extends State<Walt2HomeScreen> {
  List<ChatMessage> _messages = [];
  final TextEditingController _promptController = TextEditingController();
  late ApiService _apiService;
  bool _isAnalyzing = false;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService;
    _addWaltMessage(widget.initialMessage); // Initial message is now from API response
    // No more conditional loadStory() in initState
  }

  @override
  void dispose() {
    _apiService.closeClient();
    _promptController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _addMessage(String text, ChatMessageType type) {
    setState(() {
      _messages.add(ChatMessage(text: text, type: type));
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    });
  }

  void _addWaltMessage(String text) {
    _addMessage(text, ChatMessageType.walt);
  }

  void _addUserMessage(String text) {
    _addMessage(text, ChatMessageType.user);
  }

  Future<void> _analyzePrompt() async {
    String userInput = _promptController.text.trim();
    if (userInput.isEmpty) return;

    _addUserMessage(userInput);

    setState(() {
      _isAnalyzing = true;
    });

    try {
      final responseMessage = await _apiService.analyzePrompt(userInput);
      _addWaltMessage(responseMessage);
      setState(() {
        _isAnalyzing = false;
      });
      _promptController.clear();
    } catch (e) {
      print("Error in _analyzePrompt: $e");
      _addWaltMessage("Error analyzing prompt: $e");
      setState(() {
        _isAnalyzing = false;
      });
    }
  }

  // --- File Saving and Loading ---

  Future<String> _getFilePath() async {
    final directory = await getApplicationDocumentsDirectory();
    return '${directory.path}/walt_biography.txt'; // Default file name
  }

  Future<void> saveStory() async {
    setState(() {
      _isAnalyzing = true; // Use analyzing state for saving as well for UI feedback
    });
    try {
      final file = File(await _getFilePath());
      String storyText = _messages.where((message) => message.type == ChatMessageType.walt).map((message) => message.text).join("\n\n");
      await file.writeAsString(storyText);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Story saved locally!")),
      );
    } catch (e) {
      print("Error saving story: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error saving story: $e")),
      );
    } finally {
      setState(() {
        _isAnalyzing = false;
      });
    }
  }

  Future<void> loadStory() async {
    setState(() {
      _isAnalyzing = true; // Use analyzing state for loading as well for UI feedback
    });
    try {
      final filePath = await _getFilePath(); // Get file path
      print("Loading story from file path: $filePath"); // Debug print file path
      final file = File(filePath);
      if (await file.exists()) {
        print("Story file exists!"); // Debug print if file exists
        final story = await file.readAsString();
        print("Story content loaded: ${story.substring(0, story.length > 200 ? 200 : story.length)}..."); // Debug print loaded content (truncated)
        setState(() {
          _messages.clear();
          _messages.addAll(story.split("\n\n").map((text) => ChatMessage(text: text, type: ChatMessageType.walt)).toList());
          print("Messages after loading: ${_messages.length} messages"); // Debug print message count after loading
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Story loaded from local file!")),
        );
      } else {
        print("Story file does NOT exist."); // Debug print if file doesn't exist
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("No story file found locally.")),
        );
      }
    } catch (e) {
      print("Error loading story: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error loading story: $e")),
      );
    } finally {
      setState(() {
        _isAnalyzing = false;
      });
    }
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Walt the auto-Biographer'),
        backgroundColor: Theme.of(context).primaryColor,
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 8.0),
            child: ElevatedButton(
              onPressed: saveStory,
              style: ElevatedButton.styleFrom(
                foregroundColor: Colors.white,
                backgroundColor: Colors.green,
              ),
              child: const Text('Save Story'),
            ),
          ),
        ],
      ),
      body: Stack(
        children: [
          Column(
            children: [
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  itemCount: _messages.length,
                  reverse: true, // Add this line to reverse the list
                  itemBuilder: (context, index) {
                    final message = _messages[index]; // No longer need to reverse index here
                    return ChatBubble(message: message);
                  },
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _promptController,
                        decoration: const InputDecoration(
                          hintText: "Tell Walt about your life...",
                          border: OutlineInputBorder(),
                        ),
                        onSubmitted: (value) => _analyzePrompt(), // Submit on Enter key
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: _analyzePrompt,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.yellow,
                        foregroundColor: Colors.grey,
                      ),
                      child: const Text("Submit"),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: ElevatedButton(
                  onPressed: _analyzePrompt, // Re-use _analyzePrompt for now
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).primaryColor,
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 50),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: const Text("Craft Biography"),
                ),
              ),
            ],
          ),
          if (_isAnalyzing)
            Positioned.fill(
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: const Center(
                  child: CircularProgressIndicator(color: Colors.white),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

enum ChatMessageType { walt, user }

class ChatMessage {
  final String text;
  final ChatMessageType type;
  ChatMessage({required this.text, required this.type});
}

class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  const ChatBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 10.0, horizontal: 16.0),
      alignment: message.type == ChatMessageType.walt ? Alignment.topLeft : Alignment.topRight,
      child: Column(
        crossAxisAlignment: message.type == ChatMessageType.walt ? CrossAxisAlignment.start : CrossAxisAlignment.end,
        children: [
          Container(
            padding: const EdgeInsets.all(12.0),
            decoration: BoxDecoration(
              color: message.type == ChatMessageType.walt ? Colors.blue[100] : Colors.yellow[200],
              borderRadius: BorderRadius.circular(12.0),
            ),
            child: Text(
              message.text,
              style: const TextStyle(color: Colors.black87),
            ),
          ),
        ],
      ),
    );
  }
}
// -- lib/walt2_home_screen.dart
